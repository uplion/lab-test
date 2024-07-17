import asyncio
import aiohttp
import time
import os
from kubernetes import client, config
from random import randint

data = {"model": "static","messages": [{"role": "user","content": "Hello"}]}

async def make_request(session, url):
    async with session.get(url) as response:
        return await response.text()

async def perform_requests(num_requests, url):
    async with aiohttp.ClientSession() as session:
        tasks = [make_request(session, url) for _ in range(num_requests)]
        await asyncio.gather(*tasks)

def get_k8s_cluster_status():
    config.load_kube_config()
    v1 = client.CoreV1Api()
    nodes = v1.list_node()
    pods = v1.list_namespaced_pod(namespace="aimodel-sample")
    return {
        "nodes": len(nodes.items),
        "pods": len(pods.items)
    }

def get_current_request(minute):
    if minute < 6: return randint(10, 50)
    elif minute < 9: return (minute - 6) * (200 - 50) / (9 - 6) + 50
    elif minute < 12: return randint(200, 400)
    elif minute < 13: return randint(150, 300)
    elif minute < 17: return randint(300, 500)
    elif minute < 19: return (19 - minute) * (500 - 200) / (19 - 17) + 100
    elif minute < 22: return randint(200, 400)
    else: return (24 - minute) * (200 - 50) / (24 - 22) + 50

async def main(duration_minutes, url):
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    
    with open("log.csv", "w") as f:
        f.write("Time,Requests,Nodes,Pods\n")
        minute = 0
        while time.time() < end_time:
            current_requests = get_current_request(minute % 24)
            loop_start = time.time()
            
            await perform_requests(current_requests, url)
            
            cluster_status = get_k8s_cluster_status()
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')},{current_requests},{cluster_status['nodes']},{cluster_status['pods']}\n")
            
            elapsed = time.time() - loop_start
            if elapsed < 60:
                await asyncio.sleep(60 - elapsed)
            minute += 1

if __name__ == "__main__":
    duration_minutes = 5  # 运行总时间
    # max_requests_per_minute = 60  # 每分钟最大请求数
    url = os.getenv("TEST_URL", "http://localhost:5000/v1/chat/completions")
    
    asyncio.run(main(duration_minutes, url))
    # asyncio.run(main(duration_minutes, max_requests_per_minute * 2, url))
    # asyncio.run(main(duration_minutes, max_requests_per_minute, url))