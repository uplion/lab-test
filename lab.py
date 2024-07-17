import asyncio
import aiohttp
import time
import os
from kubernetes import client, config

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

async def main(duration_minutes, max_requests_per_minute, url):
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    
    current_requests = max_requests_per_minute
    
    while time.time() < end_time:
        loop_start = time.time()
        
        await perform_requests(current_requests, url)
        
        cluster_status = get_k8s_cluster_status()
        print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Requests made: {current_requests}")
        print(f"Cluster status: {cluster_status}")
        
        elapsed = time.time() - loop_start
        if elapsed < 60:
            await asyncio.sleep(60 - elapsed)

if __name__ == "__main__":
    duration_minutes = 30  # 运行总时间
    max_requests_per_minute = 60  # 每分钟最大请求数
    url = os.getenv("URL", "http://localhost:8081/v1/chat/completions")
    
    asyncio.run(main(duration_minutes, max_requests_per_minute, url))
    asyncio.run(main(duration_minutes, max_requests_per_minute * 2, url))
    asyncio.run(main(duration_minutes, max_requests_per_minute, url))