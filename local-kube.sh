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
echo "Cleaning up /ver/run"
pushd /var/run
sudo rm -rf kubernetes
popd

export ALLOW_PRIVILEGED=true
export KUBELET_RESOLV_CONF=/var/run/systemd/resolve/resolv.conf
export CGROUP_DRIVER=systemd
export CONTAINER_RUNTIME_ENDPOINT=/var/run/crio/crio.sock

echo "Launching local-up-cluster"
pushd /home/tsmetana/devel/src/github.com/kubernetes/kubernetes
hack/local-up-cluster.sh -o _output/local/bin/linux/amd64/
popd

