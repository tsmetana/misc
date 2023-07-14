echo -n "Checking crio daemon status: "
sudo systemctl is-active crio
res=$?

if [[ $res != 0 ]] then
	echo "Starting crio"
	sudo systemctl start crio
fi

echo "Cleaning up /tmp"
pushd /tmp
sudo rm -rf *.log local-up-cluster.sh.*
popd
echo "Cleaning up /var/run"
pushd /var/run
sudo rm -rf kubernetes
popd

if [[ -f /var/run/systemd/resolve/resolv.conf ]]; then
	export KUBELET_RESOLV_CONF=/var/run/systemd/resolve/resolv.conf
fi

export ALLOW_PRIVILEGED=true
export CGROUP_DRIVER=systemd
export CONTAINER_RUNTIME_ENDPOINT=/var/run/crio/crio.sock
export PATH=${HOME}/devel/src/github.com/kubernetes/kubernetes/third_party/etcd:$PATH

echo "Launching local-up-cluster"
pushd ${HOME}/devel/src/github.com/kubernetes/kubernetes
hack/local-up-cluster.sh -o _output/local/bin/linux/amd64/
popd

