#!/usr/bin/env python3
"""
BroadenAgentic框架快速测试
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.llm import LLMFactory, LLMFactoryConfig


async def quick_test():
    """快速测试"""
    print("🚀 BroadenAgentic框架快速测试")
    print("=" * 40)
    
    api_key = "sk-9b6f66d94dd249dfb7a7416cc270ce4d"
    
    # 测试连通性
    print("\n🔍 连通性测试")
    
    # 本地模型测试
    print("🏠 测试本地模型...")
    try:
        local_config = LLMFactoryConfig(
            preferred_mode="local",
            local_model_name="qwen3:8b"
        )
        local_factory = LLMFactory(local_config)
        local_llm = await local_factory.create_llm()
        
        is_healthy = await local_llm.health_check()
        print(f"   本地模型: {'✅ 正常' if is_healthy else '❌ 异常'}")
        
        if is_healthy:
            result = await local_llm.generate("Hello", max_tokens=10)
            print(f"   测试响应: {result.text[:50]}...")
            print(f"   使用Token: {result.tokens_used}")
            
    except Exception as e:
        print(f"   本地模型失败: {e}")
    
    # 云端模型测试
    print("\n☁️ 测试云端模型...")
    try:
        cloud_config = LLMFactoryConfig(
            preferred_mode="cloud",
            cloud_model_name="qwen-plus",
            api_key=api_key
        )
        cloud_factory = LLMFactory(cloud_config)
        cloud_llm = await cloud_factory.create_llm()
        
        is_healthy = await cloud_llm.health_check()
        print(f"   云端模型: {'✅ 正常' if is_healthy else '❌ 异常'}")
        
        if is_healthy:
            result = await cloud_llm.generate("Hello", max_tokens=10)
            print(f"   测试响应: {result.text[:50]}...")
            print(f"   使用Token: {result.tokens_used}")
            
    except Exception as e:
        print(f"   云端模型失败: {e}")
    
    # Token监控测试
    print("\n🔢 Token监控测试")
    try:
        cloud_llm.reset_token_usage()
        
        questions = [
            "什么是人工智能？",
            "什么是机器学习？"
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"\n📝 问题 {i}: {question}")
            result = await cloud_llm.generate(question)
            print(f"   响应: {result.text[:100]}...")
            print(f"   Token: {result.tokens_used}")
        
        # 显示Token统计
        token_usage = cloud_llm.get_token_usage()
        print(f"\n📊 Token统计:")
        print(f"   总Token: {token_usage['total_tokens_used']}")
        print(f"   总请求: {token_usage['total_requests']}")
        print(f"   平均Token/请求: {token_usage['average_tokens_per_request']:.1f}")
        
    except Exception as e:
        print(f"   Token监控测试失败: {e}")
    
    print("\n✅ 快速测试完成！")


if __name__ == "__main__":
    asyncio.run(quick_test()) 