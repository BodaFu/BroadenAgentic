#!/usr/bin/env python3
"""
BroadenAgentic框架演示 - 优化版本
展示本地Ollama和云端Qwen API的使用，包含Token监控
"""

import asyncio
import sys
import os
import time
from typing import Dict, Any, Callable

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.llm import LLMFactory, LLMFactoryConfig, LLMConfig
from app.core.agent import AgentConfig, AgentBase
from app.core.constraint import InputTypeConstraint, OutputTypeConstraint, OutputCriterion


class DemoFramework:
    """BroadenAgentic框架演示类"""
    
    def __init__(self):
        self.api_key = "sk-9b6f66d94dd249dfb7a7416cc270ce4d"
        self.demo_modules = {
            "1": ("连通性测试", self.test_connectivity),
            "2": ("本地模型样例", self.demo_local_model),
            "3": ("云端模型样例", self.demo_cloud_model),
            "4": ("性能对比样例", self.demo_performance_comparison),
            "5": ("Agent样例", self.demo_agent),
            "6": ("Token监控样例", self.demo_token_monitoring),
            "7": ("运行所有样例", self.run_all_demos)
        }
    
    def show_menu(self):
        """显示菜单"""
        print("\n🎯 BroadenAgentic框架演示")
        print("=" * 50)
        print("请选择要运行的测试项目：")
        print()
        
        for key, (name, _) in self.demo_modules.items():
            print(f"  {key}. {name}")
        
        print("\n  0. 退出")
        print("=" * 50)
    
    async def run_demo(self, demo_name: str, demo_func: Callable):
        """运行演示"""
        print(f"\n🚀 开始运行: {demo_name}")
        print("-" * 40)
        
        try:
            await demo_func()
            print(f"✅ {demo_name} 运行完成")
        except Exception as e:
            print(f"❌ {demo_name} 运行失败: {e}")
            import traceback
            traceback.print_exc()
        
        print("-" * 40)
    
    async def test_connectivity(self):
        """测试本地和云端模型连通性"""
        print("🔍 连通性测试")
        
        # 测试本地模型
        print("\n🏠 测试本地Ollama模型...")
        try:
            local_config = LLMFactoryConfig(
                preferred_mode="local",
                local_model_name="qwen3:8b"
            )
            local_factory = LLMFactory(local_config)
            local_llm = await local_factory.create_llm()
            
            # 健康检查
            is_healthy = await local_llm.health_check()
            print(f"   本地模型健康状态: {'✅ 正常' if is_healthy else '❌ 异常'}")
            
            if is_healthy:
                # 简单测试
                result = await local_llm.generate("Hello", max_tokens=10)
                print(f"   测试响应: {result.text[:50]}...")
                print(f"   使用Token数: {result.tokens_used}")
            
        except Exception as e:
            print(f"   本地模型连接失败: {e}")
        
        # 测试云端模型
        print("\n☁️ 测试云端Qwen API...")
        try:
            cloud_config = LLMFactoryConfig(
                preferred_mode="cloud",
                cloud_model_name="qwen-plus",
                api_key=self.api_key
            )
            cloud_factory = LLMFactory(cloud_config)
            cloud_llm = await cloud_factory.create_llm()
            
            # 健康检查
            is_healthy = await cloud_llm.health_check()
            print(f"   云端模型健康状态: {'✅ 正常' if is_healthy else '❌ 异常'}")
            
            if is_healthy:
                # 简单测试
                result = await cloud_llm.generate("Hello", max_tokens=10)
                print(f"   测试响应: {result.text[:50]}...")
                print(f"   使用Token数: {result.tokens_used}")
            
        except Exception as e:
            print(f"   云端模型连接失败: {e}")
    
    async def demo_local_model(self):
        """本地模型样例"""
        print("🏠 本地模型样例")
        
        # 创建本地LLM
        config = LLMFactoryConfig(
            preferred_mode="local",
            local_model_name="qwen3:8b"
        )
        factory = LLMFactory(config)
        llm = await factory.create_llm()
        
        # 重置Token统计
        llm.reset_token_usage()
        
        # 测试问题
        questions = [
            "请简单介绍一下人工智能",
            "什么是机器学习？",
            "解释一下深度学习的基本概念"
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"\n📝 问题 {i}: {question}")
            
            start_time = time.time()
            result = await llm.generate(question)
            end_time = time.time()
            
            print(f"   ⏱️ 响应时间: {end_time - start_time:.2f}秒")
            print(f"   🔢 使用Token数: {result.tokens_used}")
            print(f"   📄 回答: {result.text[:100]}...")
        
        # 显示Token统计
        token_usage = llm.get_token_usage()
        print(f"\n📊 Token使用统计:")
        print(f"   总Token数: {token_usage['total_tokens_used']}")
        print(f"   总请求数: {token_usage['total_requests']}")
        print(f"   平均Token/请求: {token_usage['average_tokens_per_request']:.1f}")
    
    async def demo_cloud_model(self):
        """云端模型样例"""
        print("☁️ 云端模型样例")
        
        # 创建云端LLM
        config = LLMFactoryConfig(
            preferred_mode="cloud",
            cloud_model_name="qwen-plus",
            api_key=self.api_key
        )
        factory = LLMFactory(config)
        llm = await factory.create_llm()
        
        # 重置Token统计
        llm.reset_token_usage()
        
        # 测试问题
        questions = [
            "请简单介绍一下人工智能",
            "什么是机器学习？",
            "解释一下深度学习的基本概念"
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"\n📝 问题 {i}: {question}")
            
            start_time = time.time()
            result = await llm.generate(question)
            end_time = time.time()
            
            print(f"   ⏱️ 响应时间: {end_time - start_time:.2f}秒")
            print(f"   🔢 使用Token数: {result.tokens_used}")
            print(f"   📄 回答: {result.text[:100]}...")
        
        # 显示Token统计
        token_usage = llm.get_token_usage()
        print(f"\n📊 Token使用统计:")
        print(f"   总Token数: {token_usage['total_tokens_used']}")
        print(f"   总请求数: {token_usage['total_requests']}")
        print(f"   平均Token/请求: {token_usage['average_tokens_per_request']:.1f}")
    
    async def demo_performance_comparison(self):
        """性能对比样例"""
        print("⚡ 性能对比样例")
        
        test_question = "请解释什么是机器学习，并举例说明其应用场景"
        
        # 本地模型测试
        print("\n🏠 本地模型测试...")
        local_config = LLMFactoryConfig(
            preferred_mode="local",
            local_model_name="qwen3:8b"
        )
        local_factory = LLMFactory(local_config)
        local_llm = await local_factory.create_llm()
        local_llm.reset_token_usage()
        
        start_time = time.time()
        local_result = await local_llm.generate(test_question)
        local_time = time.time() - start_time
        
        local_token_usage = local_llm.get_token_usage()
        print(f"   ⏱️ 响应时间: {local_time:.2f}秒")
        print(f"   🔢 使用Token数: {local_result.tokens_used}")
        print(f"   📊 总Token统计: {local_token_usage['total_tokens_used']}")
        
        # 云端模型测试
        print("\n☁️ 云端模型测试...")
        cloud_config = LLMFactoryConfig(
            preferred_mode="cloud",
            cloud_model_name="qwen-plus",
            api_key=self.api_key
        )
        cloud_factory = LLMFactory(cloud_config)
        cloud_llm = await cloud_factory.create_llm()
        cloud_llm.reset_token_usage()
        
        start_time = time.time()
        cloud_result = await cloud_llm.generate(test_question)
        cloud_time = time.time() - start_time
        
        cloud_token_usage = cloud_llm.get_token_usage()
        print(f"   ⏱️ 响应时间: {cloud_time:.2f}秒")
        print(f"   🔢 使用Token数: {cloud_result.tokens_used}")
        print(f"   📊 总Token统计: {cloud_token_usage['total_tokens_used']}")
        
        # 性能对比
        print(f"\n📈 性能对比:")
        print(f"   本地模式: {local_time:.2f}秒, {local_result.tokens_used} tokens")
        print(f"   云端模式: {cloud_time:.2f}秒, {cloud_result.tokens_used} tokens")
        print(f"   速度差异: {cloud_time/local_time:.2f}x")
        print(f"   Token效率: {local_result.tokens_used/cloud_result.tokens_used:.2f}x")
    
    async def demo_agent(self):
        """Agent样例"""
        print("🤖 Agent样例")
        
        # 创建LLM工厂
        factory_config = LLMFactoryConfig(
            preferred_mode="auto",
            local_model_name="qwen3:8b",
            cloud_model_name="qwen-plus",
            api_key=self.api_key
        )
        factory = LLMFactory(factory_config)
        llm = await factory.create_llm()
        
        # 重置Token统计
        llm.reset_token_usage()
        
        # 创建输入约束
        input_constraints = [
            InputTypeConstraint(
                name="topic",
                data_type="string",
                min_length=1,
                max_length=200,
                description="要分析的主题"
            )
        ]
        
        # 创建输出约束
        output_constraints = [
            OutputTypeConstraint(
                name="analysis",
                data_type="string",
                description="分析结果"
            )
        ]
        
        # 创建输出标准
        output_criterion = OutputCriterion(
            name="质量评估",
            description="输出应该准确、完整且有用",
            min_score=0.7
        )
        
        # 创建Agent配置
        agent_config = AgentConfig(
            name="智能分析Agent",
            description="分析给定主题并提供专业见解",
            input_constraints=input_constraints,
            output_constraints=output_constraints,
            output_criterion=output_criterion
        )
        
        # 创建Agent
        agent = AgentBase(agent_config, llm)
        
        # 测试主题
        topics = [
            "人工智能在医疗领域的应用",
            #"机器学习在金融行业的应用",
            #"深度学习在图像识别中的作用"
        ]
        
        for i, topic in enumerate(topics, 1):
            print(f"\n📝 主题 {i}: {topic}")
            
            try:
                result = await agent.execute(topic)
                print(f"   📄 分析结果: {result[:150]}...")
                
                # 获取Agent状态
                status = agent.get_status()
                print(f"   📈 执行次数: {status['execution_count']}")
                print(f"   📊 平均分数: {status['performance_metrics']['average_score']:.2f}")
                print(f"   🔢 总Token数: {status['performance_metrics']['total_tokens_used']}")
                
            except Exception as e:
                print(f"   ❌ 执行失败: {e}")
        
        # 显示最终统计
        final_status = agent.get_status()
        print(f"\n📊 Agent最终统计:")
        print(f"   总执行次数: {final_status['performance_metrics']['total_executions']}")
        print(f"   成功执行次数: {final_status['performance_metrics']['successful_executions']}")
        print(f"   平均分数: {final_status['performance_metrics']['average_score']:.2f}")
        print(f"   平均响应时间: {final_status['performance_metrics']['average_response_time']:.2f}秒")
        print(f"   总Token使用: {final_status['performance_metrics'].get('total_tokens_used', 0)}")
        print(f"   平均Token/执行: {final_status['performance_metrics'].get('average_tokens_per_execution', 0):.1f}")
    
    async def demo_token_monitoring(self):
        """Token监控样例"""
        print("🔍 Token监控样例")
        
        # 创建LLM
        config = LLMFactoryConfig(
            preferred_mode="cloud",
            cloud_model_name="qwen-plus",
            api_key=self.api_key
        )
        factory = LLMFactory(config)
        llm = await factory.create_llm()
        
        # 重置Token统计
        llm.reset_token_usage()
        
        print("📊 初始Token统计:")
        initial_usage = llm.get_token_usage()
        print(f"   总Token数: {initial_usage['total_tokens_used']}")
        print(f"   总请求数: {initial_usage['total_requests']}")
        
        # 执行多个请求
        requests = [
            "请简单介绍一下人工智能",
            "什么是机器学习？",
            "解释一下深度学习",
            "什么是神经网络？",
            "什么是自然语言处理？"
        ]
        
        print(f"\n🚀 执行 {len(requests)} 个请求...")
        
        for i, request in enumerate(requests, 1):
            print(f"\n📝 请求 {i}: {request}")
            
            result = await llm.generate(request)
            
            # 实时显示Token使用情况
            current_usage = llm.get_token_usage()
            print(f"   🔢 本次Token: {result.tokens_used}")
            print(f"   📊 累计Token: {current_usage['total_tokens_used']}")
            print(f"   📈 平均Token/请求: {current_usage['average_tokens_per_request']:.1f}")
        
        # 最终统计
        final_usage = llm.get_token_usage()
        print(f"\n📊 最终Token统计:")
        print(f"   总Token数: {final_usage['total_tokens_used']}")
        print(f"   总请求数: {final_usage['total_requests']}")
        print(f"   平均Token/请求: {final_usage['average_tokens_per_request']:.1f}")
        
        # 估算成本（假设每1000 tokens $0.01）
        estimated_cost = final_usage['total_tokens_used'] * 0.01 / 1000
        print(f"   💰 估算成本: ${estimated_cost:.4f}")
    
    async def run_all_demos(self):
        """运行所有样例"""
        print("🎯 运行所有样例")
        
        demos = [
            ("连通性测试", self.test_connectivity),
            ("本地模型样例", self.demo_local_model),
            ("云端模型样例", self.demo_cloud_model),
            ("性能对比样例", self.demo_performance_comparison),
            ("Agent样例", self.demo_agent),
            ("Token监控样例", self.demo_token_monitoring)
        ]
        
        for name, func in demos:
            await self.run_demo(name, func)
            print()  # 添加空行分隔
    
    async def run(self):
        """运行演示框架"""
        while True:
            self.show_menu()
            
            try:
                choice = input("\n请输入选择 (0-7): ").strip()
                
                if choice == "0":
                    print("👋 再见！")
                    break
                
                if choice in self.demo_modules:
                    name, func = self.demo_modules[choice]
                    await self.run_demo(name, func)
                else:
                    print("❌ 无效选择，请重新输入")
                    
            except KeyboardInterrupt:
                print("\n👋 再见！")
                break
            except Exception as e:
                print(f"❌ 发生错误: {e}")


async def main():
    """主函数"""
    demo = DemoFramework()
    await demo.run()


if __name__ == "__main__":
    asyncio.run(main()) 