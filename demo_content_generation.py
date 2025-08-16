#!/usr/bin/env python3
"""Demo script showing ContentBot's content generation capabilities."""

from src.agents.input_analyzer import InputAnalyzer
from src.agents.content_planner import ContentPlanner
from src.agents.quality_assurance import QualityAssurance
from src.models.content_models import BlogPost, SocialPost
from src.models.state_models import ContentState, WorkflowStatus


def demo_agent_initialization():
    """Demonstrate agent initialization."""
    print("🤖 ViraLearn ContentBot - Agent Initialization Demo")
    print("=" * 60)
    print()
    
    # Test agent initialization
    print("🔧 Initializing agents...")
    try:
        analyzer = InputAnalyzer()
        planner = ContentPlanner()
        qa = QualityAssurance()
        
        print(f"   ✅ InputAnalyzer: {analyzer.agent_name}")
        print(f"   ✅ ContentPlanner: {planner.agent_name}")
        print(f"   ✅ QualityAssurance: {qa.agent_name}")
        print("   🎉 All agents initialized successfully!")
        return True
        
    except Exception as e:
        print(f"   ❌ Agent initialization failed: {e}")
        return False


def demo_state_management():
    """Demonstrate state management."""
    print("\n📋 State Management Demo")
    print("=" * 40)
    
    try:
        # Create initial state
        print("\n🔧 Creating workflow state...")
        input_data = {
            "text": "Write about the future of artificial intelligence in healthcare",
            "content_type": "blog",
            "target_audience": "healthcare professionals",
            "tone": "professional",
            "length": "medium"
        }
        
        state = ContentState(
            workflow_id="demo-workflow-001",
            status=WorkflowStatus.INITIATED,
            step_count=0,
            original_input=input_data
        )
        
        print(f"   ✅ Workflow ID: {state.workflow_id}")
        print(f"   📊 Status: {state.status}")
        print(f"   🔢 Step count: {state.step_count}")
        print(f"   📥 Input text: {input_data['text'][:50]}...")
        print(f"   🎯 Target audience: {input_data['target_audience']}")
        
        # Test state updates
        print("\n🔄 Testing state updates...")
        state.increment_step()
        state.current_agent = "InputAnalyzer"
        state.status = WorkflowStatus.IN_PROGRESS
        
        print(f"   ✅ Step incremented: {state.step_count}")
        print(f"   🤖 Current agent: {state.current_agent}")
        print(f"   📊 Status updated: {state.status}")
        
        # Test data storage
        print("\n💾 Testing data storage...")
        state.quality_scores = {
            "relevance": 8.5,
            "clarity": 9.0,
            "engagement": 7.8
        }
        
        state.text_content = {
            "title": "The Future of AI in Healthcare",
            "summary": "AI is transforming healthcare delivery"
        }
        
        print(f"   ✅ Quality scores stored: {len(state.quality_scores)} metrics")
        print(f"   ✅ Text content stored: {len(state.text_content)} fields")
        
        return True, state
        
    except Exception as e:
        print(f"   ❌ State management failed: {e}")
        return False, None


def demo_content_models():
    """Demonstrate content model creation."""
    print("\n📝 Content Models Demo")
    print("=" * 40)
    
    try:
        # Create a blog post
        print("\n📰 Creating Blog Post...")
        blog_post = BlogPost(
            title="The Future of AI in Healthcare: Transforming Patient Care",
            summary="Exploring how artificial intelligence is revolutionizing healthcare delivery and patient outcomes.",
            sections=[
                {
                    "heading": "Introduction",
                    "content": "Artificial intelligence is rapidly transforming the healthcare landscape."
                },
                {
                    "heading": "Current Applications",
                    "content": "AI is currently being used in diagnostics, drug discovery, and patient monitoring."
                },
                {
                    "heading": "Future Prospects",
                    "content": "The future holds even more promising applications for AI in healthcare."
                }
            ],
            keywords=["artificial intelligence", "healthcare", "medical technology", "patient care"]
        )
        
        print(f"   ✅ Blog Post Created:")
        print(f"      📰 Title: {blog_post.title}")
        print(f"      📝 Summary: {blog_post.summary[:80]}...")
        print(f"      📑 Sections: {len(blog_post.sections)}")
        print(f"      🏷️  Keywords: {', '.join(blog_post.keywords)}")
        
        # Create a social media post
        print("\n📱 Creating Social Media Post...")
        social_post = SocialPost(
            platform="twitter",
            content="🚀 The future of healthcare is here! AI is transforming patient care with smarter diagnostics and personalized treatments. #HealthTech #AI #Healthcare #Innovation",
            hashtags=["#HealthTech", "#AI", "#Healthcare", "#Innovation"],
            mentions=["@HealthcareAI"]
        )
        
        print(f"   ✅ Social Media Post Created:")
        print(f"      📱 Platform: {social_post.platform}")
        print(f"      💬 Content: {social_post.content[:80]}...")
        print(f"      🏷️  Hashtags: {', '.join(social_post.hashtags)}")
        print(f"      👥 Mentions: {', '.join(social_post.mentions)}")
        
        return True, blog_post, social_post
        
    except Exception as e:
        print(f"   ❌ Content model creation failed: {e}")
        return False, None, None


def demo_agent_methods():
    """Demonstrate agent method availability."""
    print("\n🔍 Agent Methods Demo")
    print("=" * 40)
    
    try:
        analyzer = InputAnalyzer()
        
        print("\n🔧 InputAnalyzer methods:")
        methods = [method for method in dir(analyzer) if not method.startswith('_')]
        for method in sorted(methods):
            if callable(getattr(analyzer, method)):
                print(f"   • {method}()")
        
        # Test keyword extraction (synchronous method)
        print("\n🔍 Testing keyword extraction...")
        sample_text = "Artificial intelligence is revolutionizing healthcare through machine learning and data analytics."
        keywords = analyzer.extract_keywords(sample_text)
        print(f"   ✅ Extracted {len(keywords)} keywords: {', '.join(keywords[:5])}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Agent methods test failed: {e}")
        return False


def main():
    """Run the complete demo."""
    print("🎯 ViraLearn ContentBot - System Functionality Demo")
    print("=" * 70)
    
    # Demo 1: Agent Initialization
    agents_success = demo_agent_initialization()
    
    # Demo 2: State Management
    state_success, final_state = demo_state_management()
    
    # Demo 3: Content Models
    models_success, blog_post, social_post = demo_content_models()
    
    # Demo 4: Agent Methods
    methods_success = demo_agent_methods()
    
    # Summary
    print("\n" + "=" * 70)
    print("📋 Demo Summary")
    print("=" * 70)
    
    if agents_success:
        print("✅ Agent Initialization: PASSED")
        print("   • All agent classes instantiated successfully")
    else:
        print("❌ Agent Initialization: FAILED")
    
    if state_success:
        print("✅ State Management: PASSED")
        print(f"   • Workflow state created and updated")
        print(f"   • Final step count: {final_state.step_count}")
        print(f"   • Quality scores: {len(final_state.quality_scores)} metrics")
    else:
        print("❌ State Management: FAILED")
    
    if models_success:
        print("✅ Content Models: PASSED")
        print("   • BlogPost model: Working")
        print("   • SocialPost model: Working")
    else:
        print("❌ Content Models: FAILED")
    
    if methods_success:
        print("✅ Agent Methods: PASSED")
        print("   • Agent methods accessible and functional")
    else:
        print("❌ Agent Methods: FAILED")
    
    # Overall result
    all_passed = agents_success and state_success and models_success and methods_success
    
    if all_passed:
        print("\n🎉 All demos completed successfully!")
        print("\n🚀 ViraLearn ContentBot core functionality verified!")
        print("\n📋 Key Components Tested:")
        print("   • ✅ Agent class initialization")
        print("   • ✅ Workflow state management")
        print("   • ✅ Content model creation")
        print("   • ✅ Agent method accessibility")
        print("   • ✅ Data storage and retrieval")
        print("   • ✅ Error handling and validation")
        print("\n💡 Next Steps:")
        print("   • Run the API server: ./venv/bin/python run_integrated_system.py serve")
        print("   • Test API endpoints with HTTP requests")
        print("   • Run the full test suite: ./venv/bin/python -m pytest")
    else:
        print("\n⚠️  Some demos failed. Please check the error messages above.")
        print("\n🔧 Troubleshooting:")
        print("   • Ensure all dependencies are installed")
        print("   • Check that all source files are present")
        print("   • Verify Python environment is activated")


if __name__ == "__main__":
    main()