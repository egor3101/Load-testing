import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random
from fake_useragent import UserAgent
import json
from collections import defaultdict
import socket

# Конфигурация
TARGET_URL = "https://travel-click.ru/login.page"
REQUESTS_COUNT = 1500  # Увеличиваем нагрузку
THREADS_COUNT = 150  # Больше потоков
TEST_DURATION = 180  # 3 минуты
REQUEST_TIMEOUT = (3.05, 15)  # Увеличили таймаут

# Инициализация
ua = UserAgent()
session = requests.Session()


def get_random_headers():
    return {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Referer': 'https://travel-click.ru/',
        'Connection': 'keep-alive'
    }


def enhanced_send_request(url, request_num):
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
        'server_ip': None,
        'response_headers': None
    }

    try:
        # Измерение DNS и получение IP сервера
        start_dns = time.time()
        hostname = url.split('/')[2]
        server_ip = socket.gethostbyname(hostname)
        metrics.update({
            'dns_time': time.time() - start_dns,
            'server_ip': server_ip
        })

        # Отправка запроса
        start_time = time.time()
        response = session.get(
            url,
            headers=get_random_headers(),
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True
        )

        metrics.update({
            'status': response.status_code,
            'time': time.time() - start_time,
            'success': True,
            'response_size': len(response.content),
            'url': response.url,
            'redirects': len(response.history),
            'response_headers': dict(response.headers)
        })

    except Exception as e:
        error_type = type(e).__name__
        error_details = str(e) or "No details"

        # Специальная обработка для None-ошибок
        if error_details == "None":
            error_details = "Empty error message"
            error_type = "EmptyError"

        metrics.update({
            'error_type': error_type,
            'error_details': error_details,
            'time': time.time() - start_time if 'start_time' in locals() else None
        })

    return metrics


def analyze_results(metrics):
    successful = [m for m in metrics if m['success']]
    failed = [m for m in metrics if not m['success']]

    print("\n📊 ENHANCED TEST RESULTS:")
    print(f"✅ Successful: {len(successful)}/{len(metrics)} ({len(successful) / len(metrics) * 100:.1f}%)")

    if successful:
        avg_time = sum(m['time'] for m in successful) / len(successful)
        avg_dns = sum(m['dns_time'] for m in successful) / len(successful)
        print(f"⏱ Avg response: {avg_time:.3f}s | DNS: {avg_dns:.3f}s")
        print(f"🔗 Avg size: {sum(m['response_size'] for m in successful) / len(successful) / 1024:.2f} KB")

    if failed:
        print("\n🔍 FAILURE ANALYSIS:")
        error_types = defaultdict(list)
        for m in failed:
            error_types[m['error_type']].append(m)

        for error_type, errors in sorted(error_types.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"\n❌ {error_type}: {len(errors)} errors")

            # Анализ первых 3 ошибок каждого типа
            for error in errors[:3]:
                details = error['error_details']
                print(f"   - {details[:120]}" if details else "   - No details")

                # Дополнительная информация для ConnectionError
                if error_type == 'ConnectionError':
                    print(f"     Request #{error['request_num']} | Time: {error['time']:.3f}s")


def run_load_test():
    print(f"🔥 STARTING LOAD TEST: {TARGET_URL}")
    print(f"⚡ Configuration: {REQUESTS_COUNT} requests, {THREADS_COUNT} threads")

    metrics = []
    start_test_time = time.time()

    with ThreadPoolExecutor(max_workers=THREADS_COUNT) as executor:
        futures = [executor.submit(enhanced_send_request, TARGET_URL, i) for i in range(REQUESTS_COUNT)]

        for i, future in enumerate(as_completed(futures)):
            metrics.append(future.result())

            # Вывод прогресса
            if i % 100 == 0 or i == REQUESTS_COUNT - 1:
                elapsed = time.time() - start_test_time
                error_count = len([m for m in metrics if not m['success']])
                print(
                    f"\r🚀 Progress: {i + 1}/{REQUESTS_COUNT} | "
                    f"{len(metrics)/(elapsed or 1):.1f} req/sec | "
                    f"Errors: {error_count}",
                    end=''
                )

    analyze_results(metrics)

    # Сохранение результатов
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"travelclick_test_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"\n\n📄 Full results saved to {filename}")


if __name__ == "__main__":
    run_load_test()