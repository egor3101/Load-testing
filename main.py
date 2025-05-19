import requests
from concurrent.futures import ThreadPoolExecutor
import time
from urllib.parse import urlparse
import random
from fake_useragent import UserAgent

# Инициализация генератора случайных User-Agent
ua = UserAgent()


def get_random_headers():
    return {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Connection': 'keep-alive'
    }


def send_request(url, timeout=10):
    try:
        headers = get_random_headers()
        start_time = time.time()
        response = requests.get(
            url,
            headers=headers,
            timeout=timeout,
            allow_redirects=True
        )
        duration = time.time() - start_time

        return {
            'status': response.status_code,
            'time': round(duration, 2),
            'success': response.status_code == 200,
            'url': response.url  # Финальный URL после редиректов
        }
    except Exception as e:
        return {
            'error': str(e),
            'success': False
        }


def load_test(url, num_requests=100, max_workers=10, test_duration=None):
    domain = urlparse(url).netloc
    print(f"\n🚀 Starting load test for {domain} ({url})")
    print(f"📊 Parameters: {num_requests} requests, {max_workers} concurrent workers")
    if test_duration:
        print(f"⏱ Test duration: {test_duration} seconds")

    start_test_time = time.time()
    successes = 0
    total_time = 0
    status_codes = {}
    response_times = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for i in range(num_requests):
            futures.append(executor.submit(send_request, url))

            # Добавляем небольшую случайную задержку между запуском запросов
            time.sleep(random.uniform(0.01, 0.1))

            if test_duration and (time.time() - start_test_time) > test_duration:
                print(f"\n⏰ Test duration reached, stopping after {i + 1} requests")
                break

    results = [future.result() for future in futures]

    for result in results:
        if result['success']:
            successes += 1
            total_time += result['time']
            response_times.append(result['time'])

        if 'status' in result:
            status = result['status']
            status_codes[status] = status_codes.get(status, 0) + 1

    print("\n📊 Test results:")
    print(f"✅ Successful requests: {successes}/{len(results)} ({successes / len(results) * 100:.1f}%)")
    if successes > 0:
        print(f"⏱ Average response time: {total_time / successes:.2f} seconds")
        print(f"🐢 Slowest response: {max(response_times):.2f} seconds")
        print(f"⚡ Fastest response: {min(response_times):.2f} seconds")
    print("🔢 Status codes:", status_codes)
    print(f"🌐 Final URL after redirects: {results[-1]['url'] if results else 'N/A'}")
    print(f"🕒 Total test time: {time.time() - start_test_time:.2f} seconds")


if __name__ == "__main__":
    # Настройки теста для travel-click.ru
    TARGET_URL = "https://travel-click.ru/"
    REQUESTS_COUNT = 200
    THREADS_COUNT = 20
    TEST_DURATION = 30  # в секундах (None для отключения)

    # Дополнительные URL для тестирования (если нужно)
    ADDITIONAL_PAGES = [
        "/about",
        "/contacts",
        "/offers",
        "/blog"
    ]

    # Основной тест главной страницы
    load_test(
        TARGET_URL,
        num_requests=REQUESTS_COUNT,
        max_workers=THREADS_COUNT,
        test_duration=TEST_DURATION
    )

    # Дополнительно: тестирование других страниц
    if ADDITIONAL_PAGES:
        print("\n🔍 Testing additional pages...")
        for page in ADDITIONAL_PAGES:
            page_url = f"{TARGET_URL.rstrip('/')}{page}"
            load_test(
                page_url,
                num_requests=50,  # Меньше запросов для дополнительных страниц
                max_workers=10,
                test_duration=10
            )
            time.sleep(2)  # Пауза между тестами