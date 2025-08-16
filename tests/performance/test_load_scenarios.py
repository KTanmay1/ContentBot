"""Performance and load testing scenarios for ViraLearn ContentBot."""

import asyncio
import time
import statistics
from typing import List, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta

import pytest
import httpx
import psutil
from faker import Faker

fake = Faker()


@dataclass
class PerformanceMetrics:
    """Container for performance test metrics."""
    response_times: List[float]
    success_count: int
    error_count: int
    throughput: float
    cpu_usage: float
    memory_usage: float
    start_time: datetime
    end_time: datetime
    
    @property
    def avg_response_time(self) -> float:
        return statistics.mean(self.response_times) if self.response_times else 0
    
    @property
    def p95_response_time(self) -> float:
        return statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) >= 20 else 0
    
    @property
    def p99_response_time(self) -> float:
        return statistics.quantiles(self.response_times, n=100)[98] if len(self.response_times) >= 100 else 0
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.error_count
        return (self.success_count / total * 100) if total > 0 else 0
    
    @property
    def duration(self) -> float:
        return (self.end_time - self.start_time).total_seconds()


class LoadTestRunner:
    """Runner for executing load tests against the ContentBot API."""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = "test-api-key"):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
    
    async def make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Make a single HTTP request and measure response time."""
        start_time = time.time()
        
        async with httpx.AsyncClient() as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(
                        f"{self.base_url}{endpoint}",
                        headers=self.headers,
                        timeout=30.0
                    )
                elif method.upper() == "POST":
                    response = await client.post(
                        f"{self.base_url}{endpoint}",
                        headers=self.headers,
                        json=data,
                        timeout=30.0
                    )
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                end_time = time.time()
                response_time = end_time - start_time
                
                return {
                    "success": response.status_code < 400,
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "response_data": response.json() if response.headers.get("content-type", "").startswith("application/json") else None,
                    "error": None
                }
            
            except Exception as e:
                end_time = time.time()
                response_time = end_time - start_time
                
                return {
                    "success": False,
                    "status_code": 0,
                    "response_time": response_time,
                    "response_data": None,
                    "error": str(e)
                }
    
    async def run_concurrent_requests(self, 
                                    request_func: Callable,
                                    concurrent_users: int,
                                    requests_per_user: int) -> PerformanceMetrics:
        """Run concurrent requests and collect performance metrics."""
        start_time = datetime.now()
        start_cpu = psutil.cpu_percent()
        start_memory = psutil.virtual_memory().percent
        
        response_times = []
        success_count = 0
        error_count = 0
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(concurrent_users)
        
        async def limited_request():
            async with semaphore:
                return await request_func()
        
        # Generate all tasks
        tasks = []
        for _ in range(concurrent_users * requests_per_user):
            tasks.append(limited_request())
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, Exception):
                error_count += 1
                response_times.append(30.0)  # Timeout value
            else:
                response_times.append(result["response_time"])
                if result["success"]:
                    success_count += 1
                else:
                    error_count += 1
        
        end_time = datetime.now()
        end_cpu = psutil.cpu_percent()
        end_memory = psutil.virtual_memory().percent
        
        duration = (end_time - start_time).total_seconds()
        throughput = len(results) / duration if duration > 0 else 0
        
        return PerformanceMetrics(
            response_times=response_times,
            success_count=success_count,
            error_count=error_count,
            throughput=throughput,
            cpu_usage=(start_cpu + end_cpu) / 2,
            memory_usage=(start_memory + end_memory) / 2,
            start_time=start_time,
            end_time=end_time
        )
    
    def generate_workflow_data(self) -> Dict[str, Any]:
        """Generate realistic workflow creation data."""
        return {
            "input_text": fake.paragraph(nb_sentences=5),
            "content_type": fake.random_element(["blog_post", "social_post", "article"]),
            "target_audience": fake.random_element(["general", "technical", "business", "academic"]),
            "platform": fake.random_element(["website", "linkedin", "twitter", "facebook"]),
            "tone": fake.random_element(["professional", "casual", "friendly", "authoritative"]),
            "keywords": [fake.word() for _ in range(3)]
        }
    
    def generate_content_analysis_data(self) -> Dict[str, Any]:
        """Generate realistic content analysis data."""
        return {
            "content": fake.text(max_nb_chars=1000),
            "analysis_type": fake.random_element(["sentiment", "themes", "keywords", "readability"])
        }


class PerformanceTestSuite:
    """Comprehensive performance test suite."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.runner = LoadTestRunner(base_url)
        self.results = {}
    
    async def test_health_endpoint_load(self, concurrent_users: int = 50, requests_per_user: int = 10):
        """Test health endpoint under load."""
        async def health_request():
            return await self.runner.make_request("GET", "/health")
        
        metrics = await self.runner.run_concurrent_requests(
            health_request, concurrent_users, requests_per_user
        )
        
        self.results["health_endpoint"] = metrics
        return metrics
    
    async def test_workflow_creation_load(self, concurrent_users: int = 20, requests_per_user: int = 5):
        """Test workflow creation under load."""
        async def workflow_request():
            data = self.runner.generate_workflow_data()
            return await self.runner.make_request("POST", "/api/workflows/", data)
        
        metrics = await self.runner.run_concurrent_requests(
            workflow_request, concurrent_users, requests_per_user
        )
        
        self.results["workflow_creation"] = metrics
        return metrics
    
    async def test_content_analysis_load(self, concurrent_users: int = 30, requests_per_user: int = 8):
        """Test content analysis under load."""
        async def analysis_request():
            data = self.runner.generate_content_analysis_data()
            return await self.runner.make_request("POST", "/api/content/analyze", data)
        
        metrics = await self.runner.run_concurrent_requests(
            analysis_request, concurrent_users, requests_per_user
        )
        
        self.results["content_analysis"] = metrics
        return metrics
    
    async def test_mixed_workload(self, duration_seconds: int = 60):
        """Test mixed workload scenario."""
        start_time = time.time()
        tasks = []
        
        while time.time() - start_time < duration_seconds:
            # Randomly choose endpoint
            endpoint_choice = fake.random_element([
                ("GET", "/health", None),
                ("POST", "/api/workflows/", self.runner.generate_workflow_data()),
                ("POST", "/api/content/analyze", self.runner.generate_content_analysis_data())
            ])
            
            method, endpoint, data = endpoint_choice
            task = self.runner.make_request(method, endpoint, data)
            tasks.append(task)
            
            # Add small delay to simulate realistic usage
            await asyncio.sleep(0.1)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        response_times = []
        success_count = 0
        error_count = 0
        
        for result in results:
            if isinstance(result, Exception):
                error_count += 1
                response_times.append(30.0)
            else:
                response_times.append(result["response_time"])
                if result["success"]:
                    success_count += 1
                else:
                    error_count += 1
        
        end_time = datetime.now()
        throughput = len(results) / duration_seconds
        
        metrics = PerformanceMetrics(
            response_times=response_times,
            success_count=success_count,
            error_count=error_count,
            throughput=throughput,
            cpu_usage=psutil.cpu_percent(),
            memory_usage=psutil.virtual_memory().percent,
            start_time=datetime.now() - timedelta(seconds=duration_seconds),
            end_time=end_time
        )
        
        self.results["mixed_workload"] = metrics
        return metrics
    
    def print_results(self):
        """Print formatted test results."""
        print("\n" + "="*80)
        print("PERFORMANCE TEST RESULTS")
        print("="*80)
        
        for test_name, metrics in self.results.items():
            print(f"\n{test_name.upper().replace('_', ' ')}:")
            print(f"  Duration: {metrics.duration:.2f}s")
            print(f"  Total Requests: {metrics.success_count + metrics.error_count}")
            print(f"  Success Rate: {metrics.success_rate:.1f}%")
            print(f"  Throughput: {metrics.throughput:.2f} req/s")
            print(f"  Avg Response Time: {metrics.avg_response_time*1000:.2f}ms")
            print(f"  P95 Response Time: {metrics.p95_response_time*1000:.2f}ms")
            print(f"  P99 Response Time: {metrics.p99_response_time*1000:.2f}ms")
            print(f"  CPU Usage: {metrics.cpu_usage:.1f}%")
            print(f"  Memory Usage: {metrics.memory_usage:.1f}%")
    
    def assert_performance_requirements(self):
        """Assert that performance requirements are met."""
        for test_name, metrics in self.results.items():
            # Basic performance assertions
            assert metrics.success_rate >= 95.0, f"{test_name}: Success rate {metrics.success_rate:.1f}% below 95%"
            assert metrics.avg_response_time <= 2.0, f"{test_name}: Avg response time {metrics.avg_response_time:.2f}s above 2s"
            assert metrics.p95_response_time <= 5.0, f"{test_name}: P95 response time {metrics.p95_response_time:.2f}s above 5s"
            
            # Resource usage assertions
            assert metrics.cpu_usage <= 80.0, f"{test_name}: CPU usage {metrics.cpu_usage:.1f}% above 80%"
            assert metrics.memory_usage <= 85.0, f"{test_name}: Memory usage {metrics.memory_usage:.1f}% above 85%"


# Pytest test functions
@pytest.mark.asyncio
@pytest.mark.performance
class TestPerformanceScenarios:
    """Performance test scenarios using pytest."""
    
    @pytest.fixture
    def performance_suite(self):
        return PerformanceTestSuite()
    
    async def test_light_load(self, performance_suite):
        """Test system under light load."""
        await performance_suite.test_health_endpoint_load(concurrent_users=10, requests_per_user=5)
        await performance_suite.test_workflow_creation_load(concurrent_users=5, requests_per_user=3)
        
        performance_suite.print_results()
        performance_suite.assert_performance_requirements()
    
    async def test_moderate_load(self, performance_suite):
        """Test system under moderate load."""
        await performance_suite.test_health_endpoint_load(concurrent_users=25, requests_per_user=8)
        await performance_suite.test_workflow_creation_load(concurrent_users=15, requests_per_user=5)
        await performance_suite.test_content_analysis_load(concurrent_users=20, requests_per_user=6)
        
        performance_suite.print_results()
        performance_suite.assert_performance_requirements()
    
    async def test_heavy_load(self, performance_suite):
        """Test system under heavy load."""
        await performance_suite.test_health_endpoint_load(concurrent_users=50, requests_per_user=10)
        await performance_suite.test_workflow_creation_load(concurrent_users=30, requests_per_user=8)
        await performance_suite.test_content_analysis_load(concurrent_users=40, requests_per_user=10)
        
        performance_suite.print_results()
        performance_suite.assert_performance_requirements()
    
    async def test_stress_scenario(self, performance_suite):
        """Test system under stress conditions."""
        await performance_suite.test_mixed_workload(duration_seconds=120)
        
        performance_suite.print_results()
        # Relaxed requirements for stress test
        for test_name, metrics in performance_suite.results.items():
            assert metrics.success_rate >= 90.0, f"{test_name}: Success rate {metrics.success_rate:.1f}% below 90%"
            assert metrics.avg_response_time <= 5.0, f"{test_name}: Avg response time {metrics.avg_response_time:.2f}s above 5s"
    
    async def test_endurance(self, performance_suite):
        """Test system endurance over extended period."""
        await performance_suite.test_mixed_workload(duration_seconds=300)  # 5 minutes
        
        performance_suite.print_results()
        # Check for memory leaks and performance degradation
        for test_name, metrics in performance_suite.results.items():
            assert metrics.success_rate >= 95.0, f"{test_name}: Success rate degraded to {metrics.success_rate:.1f}%"
            assert metrics.memory_usage <= 90.0, f"{test_name}: Memory usage {metrics.memory_usage:.1f}% indicates potential leak"


if __name__ == "__main__":
    # Run performance tests directly
    async def main():
        suite = PerformanceTestSuite()
        
        print("Running Performance Tests...")
        
        # Run all test scenarios
        await suite.test_health_endpoint_load()
        await suite.test_workflow_creation_load()
        await suite.test_content_analysis_load()
        await suite.test_mixed_workload(duration_seconds=60)
        
        suite.print_results()
        
        try:
            suite.assert_performance_requirements()
            print("\n✅ All performance requirements met!")
        except AssertionError as e:
            print(f"\n❌ Performance requirement failed: {e}")
    
    asyncio.run(main())