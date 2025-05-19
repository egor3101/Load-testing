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
REQUESTS_COUNT = 1000
THREADS_COUNT = 100
TEST_DURATION = 120

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


def get_request_params():
    return {
        'headers': get_random_headers(),
        'timeout': (3.05, 10),
        'allow_redirects': True,
        'verify': True
    }


def enhanced_send_request(url, request_num):
    metrics = {
        'request_num': request_num,
        'status': None,
        'time': None,
        'success': False,
        'error_type': 'None',
        'error_details': 'None',
        'response_size': 0,
        'redirects': 0,
        'dns_time': None
    }

    try:
        # Измерение DNS
        start_dns = time.time()
        try:
            hostname = url.split('/')[2]
            socket.gethostbyname(hostname)
            metrics['dns_time'] = time.time() - start_dns
        except Exception as e:
            metrics['dns_time'] = -1
            raise

        # Полный запрос
        start_time = time.time()
        response = session.get(url, **get_request_params())

        metrics.update({
            'status': response.status_code,
            'time': time.time() - start_time,
            'success': response.status_code == 200,
            'response_size': len(response.content),
            'url': response.url,
            'redirects': len(response.history),
            'error_type': 'None',
            'error_details': 'None'
        })

    except requests.exceptions.SSLError as e:
        metrics.update({
            'error_type': 'SSL Error',
            'error_details': str(e) or 'SSL Handshake failed'
        })
    except requests.exceptions.ConnectionError as e:
        metrics.update({
            'error_type': 'Connection Error',
            'error_details': str(e) or 'Connection failed'
        })
    except requests.exceptions.Timeout as e:
        metrics.update({
            'error_type': 'Timeout',
            'error_details': str(e) or 'Request timed out'
        })
    except Exception as e:
        metrics.update({
            'error_type': 'Other Error',
            'error_details': str(e) or 'Unknown error occurred'
        })

    return metrics


def safe_get_error_details(error_dict):
    details = error_dict.get('error_details', 'No details')
    if details is None:
        return 'No details'
    return str(details)[:120]


def analyze_results(metrics):
    successful = [m for m in metrics if m['success']]
    failed = [m for m in metrics if not m['success']]

    print("\n📊 DETAILED TEST RESULTS:")
    print(f"✅ Successful requests: {len(successful)}/{len(metrics)} ({len(successful) / len(metrics) * 100:.1f}%)")

    if successful:
        avg_time = sum(m['time'] for m in successful if m['time']) / len(successful)
        avg_dns = sum(m['dns_time'] for m in successful if m['dns_time'] and m['dns_time'] > 0) / max(1, len([m for m in
                                                                                                              successful
                                                                                                              if m[
                                                                                                                  'dns_time'] and
                                                                                                              m[
                                                                                                                  'dns_time'] > 0]))
        print(f"⏱ Avg response time: {avg_time:.3f}s (DNS: {avg_dns:.3f}s)")

    if failed:
        error_analysis = defaultdict(int)
        for m in failed:
            error_analysis[m.get('error_type', 'Unknown')] += 1

        print("\n🔍 Error Analysis:")
        for error_type, count in sorted(error_analysis.items(), key=lambda x: x[1], reverse=True):
            print(f"  {error_type}: {count} errors")

            examples = [m for m in failed if m.get('error_type') == error_type][:3]
            for ex in examples:
                print(f"    - {safe_get_error_details(ex)}")


def run_load_test():
    print(f"🔥 Starting ENHANCED load test for {TARGET_URL}")
    print(f"⚡ Parameters: {REQUESTS_COUNT} requests, {THREADS_COUNT} threads")

    metrics = []
    with ThreadPoolExecutor(max_workers=THREADS_COUNT) as executor:
        futures = [executor.submit(enhanced_send_request, TARGET_URL, i) for i in range(REQUESTS_COUNT)]

        for i, future in enumerate(as_completed(futures)):
            metrics.append(future.result())
            if i % 50 == 0 or i == REQUESTS_COUNT - 1:
                print(f"\r🚀 Sent {i + 1}/{REQUESTS_COUNT} requests...", end='', flush=True)

    analyze_results(metrics)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"travelclick_loadtest_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"\n📄 Full results saved to {filename}")


if __name__ == "__main__":
    run_load_test()