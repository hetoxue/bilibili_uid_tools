import asyncio
import aiohttp
import random
from bs4 import BeautifulSoup

# === 配置区 ===
BASE_URL = "https://space.bilibili.com/"
START_PREFIX = "1314"
END_SUFFIX = "4254"
OUTPUT_FILE = "1.txt"
CONCURRENCY_LIMIT = 2  # 限制同时只发2个请求，不要太猛
# 填入你浏览器里的 Cookie，能极大降低 412 概率
MY_COOKIE = "这里替换成你的完整Cookie字符串" 

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
    "Cookie": "在这填你的cookie"

}

# 信号量，控制并发数
sem = asyncio.Semaphore(CONCURRENCY_LIMIT)

async def fetch_user_info(session, middle_digits):
    uid = f"{START_PREFIX}{middle_digits}{END_SUFFIX}"
    url = f"{BASE_URL}{uid}"
    
    async with sem: # 只有拿到信号量的任务才能执行
        try:
            # 随机歇 1-3 秒，模拟真人翻页
            await asyncio.sleep(random.uniform(1, 3))
            
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    title = soup.title.string if soup.title else ""
                    
                    # 逻辑判断：包含“的个人空间”说明找到了用户
                    if "的个人空间" in title:
                        username = title.split(" 的个人空间")[0].strip()
                        result = f"{uid}: {username} 的个人空间"
                    else:
                        # 可能是 404 或者被拦截到了验证码页
                        result = f"{uid}: 的个人空间"
                    
                    print(f"[成功] UID {uid} 查询完毕")
                    return result
                
                elif response.status == 412:
                    print(f"[警告] UID {uid} 触发风控 (412)，请进一步调低并发或检查Cookie")
                    return f"{uid}: 触发风控(412)"
                else:
                    return f"{uid}: 访问异常 (Status {response.status})"
                    
        except Exception as e:
            return f"{uid}: 报错 ({str(e)})"

async def main():
    middle_range = [str(i).zfill(2) for i in range(100)]
    
    # 建议使用固定的 TCPConnector 保持连接
    conn = aiohttp.TCPConnector(limit_per_host=CONCURRENCY_LIMIT)
    async with aiohttp.ClientSession(headers=HEADERS, connector=conn) as session:
        tasks = [fetch_user_info(session, m) for m in middle_range]
        results = await asyncio.gather(*tasks)
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for line in results:
                f.write(line + "\n")
                
    print(f"\n全部任务已结束，请查看 {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())