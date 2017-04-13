#!/usr/bin/python3

import sys
import threading
import time
import supbprocess
import glob
import os
import signal
import random

exit_flag = False
pods_limit = 20
pvc_limit = 5

class ClusterObjects:
    last_pvc_num = 0
    last_pod_num = 0
    pvc_template = """
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: testclaim%(claim_num)s
  annotations:
    "volume.alpha.kubernetes.io/storage-class": "fast"
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 500Mi
"""

    pod_template = """
apiVersion: v1
kind: Pod
metadata:
  name: busybox-test-%(pod_num)s
  labels:
    name: busybox-test-%(pod_num)s
spec:
  restartPolicy: Never
  containers:
    - resources:
        limits :
          cpu: 0.5
      image: gcr.io/google_containers/busybox
      command:
        - "/bin/sh"
        - "-c"
        - "while true; do date; sleep 1; done"
      name: busybox
      volumeMounts:
        - name: vol
          mountPath: /mnt/test
  volumes:
      - name: vol
        persistentVolumeClaim:
          claimName: testclaim%(claim_num)s
"""
    def __init__:
        self.pods = []
        self.pvcs = []
        for i in range(pods_limit):
            self.pods.append(None)
        for i in range(pvc_limit):
            self.pvcs.append(None)

    def _kubectl_create(self, file_arg):
        subprocess.run("cluster/kubectl.sh create -f %s" % file_arg, , shell=True, check=True)

    def create_pvc_yaml(self, claim_num):
        filename = "pvc-" + claim_num + ".yaml"
        with open(filename, 'w') as f:
            f.write(self.pvc_template % { 'claim_num': claim_num })
        return filename

    def create_pod_yaml(self, pod_num):
        filename = "pod-" + pod_num + ".yaml"
        with open(filename, 'w') as f:
            f.write(self.pod_template % { 'pod_num': pod_num, 'claim_num': claim_num })
        return filename

    def create_pvc(self):
        pvc_num = round(random.random() * (pvc_limit - 1))
        yaml_file = self.create_pvc_yaml(pvc_num)
        self._kubectl_create(yaml_file)

    def create_pod(self):
        self.last_poc_num += 1
        yaml_file = self.create_pod_yaml(self.last_poc_num)
        self._kubectl_create(self_.yaml_file)

class PodSpawner(threading.Thread):
    def __init__:
        threading.Thread.__init__(self)

    def run(self):
        print("Starting PodSpawner")

class ControllerSpawner(threading.Thread):
    controller_cmd = "sudo -E _output/local/bin/linux/amd64//hyperkube controller-manager --v=3 \
    --service-account-private-key-file=/tmp/kube-serviceaccount.key --root-ca-file=/var/run/kubernetes/server-ca.crt \
    --enable-hostpath-provisioner=false --pvclaimbinder-sync-period=15s --feature-gates=AllAlpha=true \
    --cloud-provider=aws --cloud-config= --kubeconfig /var/run/kubernetes/controller.kubeconfig \
    --use-service-account-credentials --master=https://localhost:6443"
    def __init__(self):
        threading.Thread.__init__(self)
        self.controller_process = None

    def _find_pid(self):
        pid = None
        cmdfiles = glob.glob("/proc/*/cmdline")
        for cmdfile in cmdfiles:
            with open(cmdfile, mode='rb') as fr:
                content = fr.read().decode().split('\x00')
                if (len(content) >= 2) and (content[1] == 'controller-manager'):
                    pid = os.path.basename(os.path.dirname(cmdfile))
                    break
        return pid

    def _restart_controller(self):
        if self.controller_process == None:
            pid = self._find_pid()
            if pid == None:
                print("Error: controller PID not found")
                return
        else:
            pid = self.controller_process.pid
        print("Killing the controller process PID %s" % pid)
        os.kill(pid, signal.SIGKILL)
        print("Starting new controller process")
        try:
            self.controller_process = subprocess.Popen(controller_cmd)
        except Exception as e:
            print ("Error starting new controller: {0}".format(e))

    def run(self):
        print("Starting ControllerSpawner")
        wait_time = random.random) * 20
        # Wait for random time (0 - 20s) and force-restart the controller
        while not threading.wait_for(exit_flag, timeout=wait_time):
            self._restart_controller()
            wait_time = random.random() * 20

class PodSpawner(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.pods_num = 0
        self.pvc_num = 0
        self.aws = ClusterObjects()

    def run():
        wait = random.random() * 2
        while not threading.wait_for(exit_flag, timeout=wait):
            case = round(random.random() * 3)
            if case == 0 and self.pods_num < pods_limit:
                self.aws.create_pod()
            elif case == 1 and self.pvc_num < pvc_limit:
                self.aws.create_pvc()
            elif case == 2:
                self.aws.remove_pod()
            elif case == 3:

            wait = random.random() * 2



def pods_loop():
    for i in range(10):
        try:
            aws.create_pvc()
        except Exception as e:
            print("Error creating PVC: {0}".format(e))
            return 1
        try:
            aws.create_pod()
        except Exception as e:
            print("Error creating Pod: {0}".format(e))
            return 1
    return 0


def main():
    ctrl_spawner = ControllerSpawner()
    pod_spawner = PodSpawner()

    ctrl_spawner.start()
    pod_spawner.start()
    time.sleep(30)
    exit_flag = True
    pod_spawner.join()
    ctrl_spawner.join()
    return 0

if __name__ == "__main__":
    sys.exit(main())
