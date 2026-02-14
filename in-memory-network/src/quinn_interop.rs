use crate::network::InMemoryNetwork;
use crate::network::inbound_queue::NextPacketDelivery;
use crate::network::node::{Node, UdpEndpoint};
use crate::pcap_exporter::PcapExporter;
use crate::transmit::OwnedTransmit;
use cfg_if::cfg_if;
use parking_lot::Mutex;
use quinn::udp::{RecvMeta, Transmit};
use quinn::{AsyncUdpSocket, UdpSender};
use std::fmt::{Debug, Formatter};
use std::io;
use std::io::IoSliceMut;
use std::net::SocketAddr;
use std::pin::Pin;
use std::sync::Arc;
use std::task::{Context, Poll, ready};

// Sender
pub struct InMemoryUdpSender {
    network: Arc<InMemoryNetwork>,
    node: Arc<Node>,
    pcap_exporter: Arc<PcapExporter>,
}

impl Debug for InMemoryUdpSender {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.write_str("InMemoryUdpSender")
    }
}

impl UdpSender for InMemoryUdpSender {
    fn poll_send(
        self: Pin<&mut Self>,
        transmit: &Transmit<'_>,
        _cx: &mut Context<'_>,
    ) -> Poll<io::Result<()>> {
        InMemoryUdpSocket::send_inner(&self.network, &self.node, &self.pcap_exporter, transmit);
        Poll::Ready(Ok(()))
    }
}

// Socket
pub struct InMemoryUdpSocket {
    network: Arc<InMemoryNetwork>,
    endpoint: Arc<UdpEndpoint>,
    node: Arc<Node>,
    next_packet_delivery: Mutex<Option<Pin<Box<NextPacketDelivery>>>>,
    pcap_exporter: Arc<PcapExporter>,
}

impl Debug for InMemoryUdpSocket {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.write_str("InMemoryUdpSocket")
    }
}

impl InMemoryUdpSocket {
    pub fn from_node(
        network: Arc<InMemoryNetwork>,
        node: Arc<Node>,
        pcap_exporter: PcapExporter,
    ) -> Self {
        InMemoryUdpSocket {
            endpoint: node.udp_endpoint.as_ref().unwrap().clone(),
            node,
            network: network.clone(),
            next_packet_delivery: Mutex::new(None),
            pcap_exporter: Arc::new(pcap_exporter),
        }
    }

    /// Internal logic for sending a packet
    fn send_inner(
        network: &Arc<InMemoryNetwork>,
        node: &Arc<Node>,
        pcap: &PcapExporter,
        transmit: &Transmit,
    ) {
        assert!(transmit.segment_size.is_none());

        let source_addr = node.quic_addr();
        pcap.track_transmit(source_addr, transmit);

        let data = network.in_transit_data(
            node,
            OwnedTransmit {
                destination: transmit.destination,
                ecn: transmit.ecn,
                contents: transmit.contents.to_vec(),
                segment_size: transmit.segment_size,
            },
        );
        
        network.forward(node.clone(), data);
    }

    pub fn try_send(&self, transmit: &Transmit) -> io::Result<()> {
        Self::send_inner(&self.network, &self.node, &self.pcap_exporter, transmit);
        Ok(())
    }

    fn poll_recv_impl(
        &self,
        cx: &mut Context<'_>,
        bufs: &mut [IoSliceMut<'_>],
        meta: &mut [RecvMeta],
    ) -> Poll<io::Result<usize>> {
        let node = self.node.clone();
        let max_transmits = meta.len();
        assert!(meta.len() <= bufs.len());

        let mut lock = self.next_packet_delivery.lock();
        let delivery = lock.get_or_insert(Box::pin(NextPacketDelivery::new(
            self.endpoint.inbound.clone(),
            max_transmits,
        )));
        let delivered = ready!(delivery.as_mut().poll(cx));
        let delivered_len = delivered.len();

        let out = meta.iter_mut().zip(bufs);
        for (in_transit, (meta, buf)) in delivered.into_iter().zip(out) {
            self.network
                .tracer
                .track_read_by_host(node.id.clone(), &in_transit.data);

            let transmit = in_transit.data.transmit;

            // Meta
            meta.addr = in_transit.data.source_endpoint.addr;
            meta.ecn = transmit.ecn;
            meta.dst_ip = Some(transmit.destination.ip());
            meta.len = transmit.contents.len();
            meta.stride = transmit.segment_size.unwrap_or(meta.len);

            // Buffer
            buf[..transmit.contents.len()].copy_from_slice(&transmit.contents);

            // Track in pcap
            let source_addr = in_transit.data.source_endpoint.addr;
            self.pcap_exporter
                .track_transmit(source_addr, &transmit.as_transmit());
        }

        Poll::Ready(Ok(delivered_len))
    }
}

impl AsyncUdpSocket for InMemoryUdpSocket {
    fn create_sender(&self) -> Pin<Box<dyn UdpSender>> {
        Box::pin(InMemoryUdpSender {
            network: self.network.clone(),
            node: self.node.clone(),
            pcap_exporter: self.pcap_exporter.clone(),
        })
    }

    fn poll_recv(
        &mut self,
        cx: &mut Context<'_>,
        bufs: &mut [IoSliceMut<'_>],
        meta: &mut [RecvMeta],
    ) -> Poll<io::Result<usize>> {
        self.poll_recv_impl(cx, bufs, meta)
    }

    fn local_addr(&self) -> io::Result<SocketAddr> {
        Ok(self.endpoint.addr)
    }
}

// Receive Helper

impl InMemoryUdpSocket {
    pub async fn receive<'a>(
        &self,
        bufs_and_meta: &'a mut BufsAndMeta,
    ) -> io::Result<Vec<UdpPacket<'a>>> {
        let packets = self.receive_raw(bufs_and_meta).await?;

        let mut result = Vec::with_capacity(packets);
        for i in 0..packets {
            let meta = &bufs_and_meta.meta[i];
            let source_addr = meta.addr;
            let payload = &bufs_and_meta.bufs[i][..meta.len];

            result.push(UdpPacket {
                source_addr,
                payload,
            });
        }

        Ok(result)
    }

    pub async fn receive_raw(&self, bufs_and_meta: &mut BufsAndMeta) -> io::Result<usize> {
        let receive = UdpReceive {
            socket: self,
            result: bufs_and_meta,
        };

        receive.await
    }
}

pub struct UdpPacket<'a> {
    pub source_addr: SocketAddr,
    pub payload: &'a [u8],
}

pub struct UdpReceive<'a, 'b> {
    socket: &'a InMemoryUdpSocket,
    result: &'b mut BufsAndMeta,
}

pub struct BufsAndMeta {
    pub bufs: Vec<Vec<u8>>,
    pub meta: Vec<RecvMeta>,
}

impl BufsAndMeta {
    pub fn new(max_packet_size: usize, max_packets_per_read: usize) -> Self {
        Self {
            bufs: vec![vec![0u8; max_packet_size]; max_packets_per_read],
            meta: vec![RecvMeta::default(); max_packets_per_read],
        }
    }
}

impl Future for UdpReceive<'_, '_> {
    type Output = io::Result<usize>;

    fn poll(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output> {
        let this = &mut *self;
        let socket = this.socket;
        let bufs = &mut this.result.bufs;
        let meta = &mut this.result.meta;

        let mut bufs: Vec<_> = bufs.iter_mut().map(|b| IoSliceMut::new(b)).collect();
        socket.poll_recv_impl(cx, &mut bufs, meta)
    }
}

cfg_if! {
    if #[cfg(feature = "rt-custom")] {
        use sittard::Runtime as Rt;
        use sittard::time::Timer;
        use std::time::Instant;
        use std::net::UdpSocket;
        use quinn::{AsyncTimer, Runtime};

        pub struct RtAdapter;

        impl Debug for RtAdapter {
            fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
                write!(f, "rt-adapter")
            }
        }

        impl Runtime for RtAdapter {
            fn new_timer(&self, i: Instant) -> Pin<Box<dyn AsyncTimer>> {
                Box::pin(RtTimerAdapter { inner: Rt::active().new_timer(i) })
            }

            fn spawn(&self, future: Pin<Box<dyn Future<Output = ()> + Send>>) {
                Rt::active().spawn(future)
            }

            fn wrap_udp_socket(&self, _: UdpSocket) -> io::Result<Box<dyn AsyncUdpSocket>> {
                unimplemented!("not used")
            }

            fn now(&self) -> Instant {
                Rt::active().now()
            }
        }

        pin_project_lite::pin_project! {
            struct RtTimerAdapter {
                #[pin]
                inner: Timer
            }
        }

        impl Debug for RtTimerAdapter {
            fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
                write!(f, "rt-timer-adapter")
            }
        }

        impl AsyncTimer for RtTimerAdapter {
            fn reset(self: Pin<&mut Self>, i: Instant) {
                let this = self.project();
                this.inner.reset(i)
            }

            fn poll(self: Pin<&mut Self>, cx: &mut Context) -> Poll<()> {
                let this = self.project();
                this.inner.poll(cx)
            }
        }
    }
}