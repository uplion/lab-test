import time
import os
from kubernetes import client, config
import json
import requests
import threading

data = {"model": "static2","messages": [{"role": "user","content": "Hello"}]}

def worker(url):
    response = requests.post(url, json=data)
    print('.', end='')
    return response


def perform_requests(count, url):
    for i in range(count):
        threading.Thread(target=worker, args=(url,)).start()
        time.sleep(0.04)

def get_k8s_cluster_status():
    config.load_kube_config()
    v1 = client.CoreV1Api()
    nodes = v1.list_node()
    pods = v1.list_namespaced_pod(namespace="default", label_selector="aimodel-internel-selector=aimodel-sample")
    return {
        "nodes": len(nodes.items),
        "pods": len(pods.items)
    }

def get_hpa_info(name='keda-hpa-aimodel-sample-scaledobject'):
    config.load_kube_config()
    v1 = client.AutoscalingV1Api()
    hpa = v1.read_namespaced_horizontal_pod_autoscaler(name, "default")
    metrics = json.loads(hpa.metadata.annotations['autoscaling.alpha.kubernetes.io/current-metrics'])[0]['external']
    return {
        "min_replicas": hpa.spec.min_replicas,
        "max_replicas": hpa.spec.max_replicas,
        "current_replicas": hpa.status.current_replicas,
        "desired_replicas": hpa.status.desired_replicas,
        "currentMetrics": metrics['currentValue'],
        'currentAverageMetrics': metrics['currentAverageValue']
    }

def get_current_request(minute):
    if minute <= 4: # [2, 10]
        return minute * 2 + 2
    if minute <= 18:
        return 20
    return 4
    


def main(duration_minutes, url):
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)

    minute = 0
    while time.time() < end_time:
        minute_start = time.time()
        current_requests = get_current_request(minute)
        print(f'===== minute: {minute}, current_requests: {current_requests}')

        while time.time() < minute_start + 60:
            second_start = time.time()
            print(f"\ttime: {minute}:{second_start - minute_start:.2f} performing {current_requests} requests")
            perform_requests(current_requests, url)

            time.sleep(max(0, second_start + 1 - time.time()))  
        
        with open("log.json", "a") as f:
            f.write(json.dumps({
                "time": time.strftime('%Y-%m-%d %H:%M:%S'),
                "current_requests": current_requests,
                "cluster_status": get_k8s_cluster_status(),
                "hpa_info": get_hpa_info(),
            }) + '\n')

        minute += 1
        

            

if __name__ == "__main__":
    duration_minutes = 60
    url = os.getenv("TEST_URL", "http://172.21.0.2:30080/api/v1/chat/completions")
    
    try:
        os.remove("log.json")
    except:
        pass

    print("+ kubectl delete -f ../aimodel_test.yaml")
    os.system("kubectl delete -f ../aimodel_test.yaml")
    print("+ kubectl apply -f ../aimodel_test.yaml")
    os.system("kubectl apply -f ../aimodel_test.yaml")
    time.sleep(5)

    print("Start testing")
    main(duration_minutes, url)
    