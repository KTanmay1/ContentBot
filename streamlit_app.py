#!/usr/bin/env python3
"""
ViraLearn ContentBot - Streamlit Prototype
A comprehensive web interface for content generation using AI agents.
"""

import streamlit as st
import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional
import json
import traceback

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import ContentBot components
from src.agents.input_analyzer import InputAnalyzer
from src.agents.content_planner import ContentPlanner
from src.agents.quality_assurance import QualityAssurance
from src.agents.text_generator import TextGenerator
from src.agents.image_generator import ImageGenerator
from src.models.state_models import ContentState, WorkflowStatus
from src.models.content_models import BlogPost, SocialPost
from config.database import get_db_manager, init_database
from config.settings import get_settings
from src.core.workflow_engine import WorkflowEngine
from src.core.monitoring import SystemMonitor

# Configure Streamlit page
st.set_page_config(
    page_title="ViraLearn ContentBot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
.main-header {
    font-size: 3rem;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
}
.agent-status {
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}
.status-success {
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    color: #155724;
}
.status-error {
    background-color: #f8d7da;
    border: 1px solid #f5c6cb;
    color: #721c24;
}
.status-processing {
    background-color: #fff3cd;
    border: 1px solid #ffeaa7;
    color: #856404;
}
.metric-card {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 0.5rem;
    border: 1px solid #dee2e6;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
if 'db_connected' not in st.session_state:
    st.session_state.db_connected = False
if 'agents' not in st.session_state:
    st.session_state.agents = {}
if 'workflow_history' not in st.session_state:
    st.session_state.workflow_history = []
if 'system_monitor' not in st.session_state:
    st.session_state.system_monitor = None


class StreamlitContentBot:
    """Main ContentBot application for Streamlit."""
    
    def __init__(self):
        self.settings = get_settings()
        self.db_manager = None
        self.workflow_engine = None
        self.agents = {}
        self.system_monitor = SystemMonitor()
    
    async def initialize(self):
        """Initialize the ContentBot system."""
        try:
            # Initialize database with fallback handling
            try:
                await init_database()
                self.db_manager = get_db_manager()
                
                # Test database connection
                db_status = await self.db_manager.test_connection()
                st.session_state.db_connected = db_status
                
                if db_status:
                    print("Database initialized successfully")
                else:
                    print("Database connection failed, but continuing with fallback")
                    
            except Exception as db_error:
                print(f"Database initialization error: {db_error}")
                print("Continuing without database connection")
                st.session_state.db_connected = False
                self.db_manager = None
            
            # Get LLM provider from session state
            provider = getattr(st.session_state, 'llm_provider', 'gemini')
            
            # Initialize agents with current provider
            self.agents = {
                'input_analyzer': InputAnalyzer(),
                'content_planner': ContentPlanner(),
                'quality_assurance': QualityAssurance(),
                'text_generator': TextGenerator(provider=provider),
                'image_generator': ImageGenerator()
            }
            
            # Store the provider used for initialization
            st.session_state.agents_provider = provider
            
            # Initialize workflow engine
            self.workflow_engine = WorkflowEngine()
            
            # Store in session state
            st.session_state.agents = self.agents
            st.session_state.system_monitor = self.system_monitor
            st.session_state.initialized = True
            
            return True
            
        except Exception as e:
            st.error(f"Failed to initialize ContentBot: {str(e)}")
            st.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def generate_content(self, content_type: str, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate content using the agent workflow."""
        try:
            # Create initial content state
            input_data_with_type = input_data.copy()
            input_data_with_type["content_type"] = content_type
            
            state = ContentState(
                workflow_id=f"streamlit_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                original_input=input_data_with_type,
                status=WorkflowStatus.INITIATED
            )
            
            # Step 1: Input Analysis
            st.info("🔍 Analyzing input...")
            analyzer_result = self.agents['input_analyzer'].run(state)
            state = analyzer_result.state
            
            # Step 2: Content Planning
            st.info("📋 Planning content structure...")
            planner_result = self.agents['content_planner'].run(state)
            state = planner_result.state
            
            # Step 3: Text Generation
            st.info("✍️ Generating text content...")
            text_result = self.agents['text_generator'].run(state)
            state = text_result.state
            
            # Step 4: Image Generation (if requested)
            if input_data.get('include_images', False):
                st.info("🎨 Generating images...")
                try:
                    image_result = asyncio.run(self.agents['image_generator'].execute(state))
                    state = image_result.state
                    if state.image_content.get('generated'):
                        st.success("✅ Image generated successfully!")
                    else:
                        st.warning("⚠️ Image generation completed but no image was created")
                except Exception as img_error:
                    st.error(f"❌ Image generation failed: {str(img_error)}")
                    # Store error in state for display
                    state.image_content["error"] = str(img_error)
                    state.image_content["generated"] = None
            else:
                st.info("📝 Skipping image generation (not requested)")
            
            # Step 5: Quality Assurance
            st.info("✅ Performing quality checks...")
            qa_result = self.agents['quality_assurance'].run(state)
            state = qa_result.state
            
            # Create content model based on type
            if content_type == "blog":
                generated_content = state.text_content.get('generated', '')
                content = BlogPost(
                    title=state.text_content.get('title', 'Generated Blog Post'),
                    summary=state.text_content.get('summary', ''),
                    sections=[{"heading": "Content", "body": generated_content}],
                    keywords=state.input_analysis.get('keywords', []) if state.input_analysis else [],
                    seo_meta_description=state.text_content.get('summary', '')
                )
            elif content_type == "social":
                generated_content = state.text_content.get('generated', '')
                content = SocialPost(
                    content=generated_content,
                    platform=input_data.get('platform', 'twitter'),
                    hashtags=state.input_analysis.get('keywords', []) if state.input_analysis else []
                )
            else:
                content = None
            
            # Store in workflow history
            workflow_result = {
                'timestamp': datetime.now(),
                'content_type': content_type,
                'input_data': input_data,
                'state': state,
                'content': content,
                'success': True
            }
            
            st.session_state.workflow_history.append(workflow_result)
            
            return workflow_result
            
        except Exception as e:
            st.error(f"Content generation failed: {str(e)}")
            st.error(f"Traceback: {traceback.format_exc()}")
            
            # Store failed workflow
            workflow_result = {
                'timestamp': datetime.now(),
                'content_type': content_type,
                'input_data': input_data,
                'error': str(e),
                'success': False
            }
            
            st.session_state.workflow_history.append(workflow_result)
            return None


def render_sidebar():
    """Render the sidebar with system status and navigation."""
    st.sidebar.markdown("## 🤖 ContentBot Status")
    
    # System status
    if st.session_state.initialized:
        st.sidebar.success("✅ System Initialized")
    else:
        st.sidebar.error("❌ System Not Initialized")
    
    if st.session_state.db_connected:
        st.sidebar.success("✅ Database Connected")
    else:
        st.sidebar.warning("⚠️ Database Disconnected")
    
    # LLM Provider Selection
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🧠 LLM Provider")
    
    # Initialize LLM provider in session state if not exists
    if 'llm_provider' not in st.session_state:
        st.session_state.llm_provider = 'gemini'
    
    llm_provider = st.sidebar.selectbox(
        "Select LLM Provider:",
        ["gemini", "mistral"],
        index=0 if st.session_state.llm_provider == 'gemini' else 1,
        help="Choose between Gemini (Google) and Mistral AI for text generation"
    )
    
    # Update session state if provider changed
    if llm_provider != st.session_state.llm_provider:
        st.session_state.llm_provider = llm_provider
        # Force re-initialization of agents with new provider
        if st.session_state.initialized:
            st.session_state.initialized = False
            # Clear agents to force recreation with new provider
            if 'agents' in st.session_state:
                del st.session_state.agents
            if 'agents_provider' in st.session_state:
                del st.session_state.agents_provider
            st.rerun()
    
    # Show provider status
    if llm_provider == 'gemini':
        st.sidebar.info("🔵 Using Gemini (Google AI)")
    else:
        st.sidebar.info("🟠 Using Mistral AI")
    
    # Agent status
    st.sidebar.markdown("### Agent Status")
    if st.session_state.agents:
        for agent_name, agent in st.session_state.agents.items():
            st.sidebar.text(f"✅ {agent_name.replace('_', ' ').title()}")
    else:
        st.sidebar.text("No agents loaded")
    
    # Navigation
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Navigation")
    
    return st.sidebar.selectbox(
        "Choose a page:",
        ["🏠 Home", "📝 Blog Generator", "📱 Social Media", "📊 Monitoring", "📋 History"]
    )


def render_home_page():
    """Render the home page."""
    st.markdown('<h1 class="main-header">🤖 ViraLearn ContentBot</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    Welcome to the ViraLearn ContentBot prototype! This application demonstrates the power of AI-driven content generation using multiple specialized agents.
    
    ## 🚀 Features
    
    - **Multi-Agent System**: Specialized agents for input analysis, content planning, text generation, and quality assurance
    - **Content Types**: Support for blog posts and social media content
    - **Real-time Processing**: Watch as agents work together to create high-quality content
    - **Database Integration**: Persistent storage and retrieval of generated content
    - **System Monitoring**: Real-time monitoring of agent performance and system health
    
    ## 🛠️ How It Works
    
    1. **Input Analysis**: The system analyzes your input to understand context, sentiment, and key themes
    2. **Content Planning**: Creates a structured plan for the content based on the analysis
    3. **Text Generation**: Generates high-quality text content following the plan
    4. **Quality Assurance**: Performs final checks to ensure content quality and compliance
    
    ## 📋 Getting Started
    
    Use the sidebar to navigate to different sections:
    - **Blog Generator**: Create comprehensive blog posts
    - **Social Media**: Generate platform-specific social media content
    - **Monitoring**: View system performance and agent metrics
    - **History**: Review previously generated content
    """)
    
    # System metrics
    if st.session_state.workflow_history:
        col1, col2, col3, col4 = st.columns(4)
        
        total_workflows = len(st.session_state.workflow_history)
        successful_workflows = sum(1 for w in st.session_state.workflow_history if w.get('success', False))
        success_rate = (successful_workflows / total_workflows) * 100 if total_workflows > 0 else 0
        
        with col1:
            st.metric("Total Workflows", total_workflows)
        
        with col2:
            st.metric("Successful", successful_workflows)
        
        with col3:
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        with col4:
            recent_workflows = len([w for w in st.session_state.workflow_history 
                                  if (datetime.now() - w['timestamp']).seconds < 3600])
            st.metric("Last Hour", recent_workflows)


def render_blog_generator():
    """Render the blog generator page."""
    st.markdown("# 📝 Blog Post Generator")
    
    st.markdown("""
    Generate comprehensive blog posts using AI agents. Provide a topic and additional context,
    and watch as the system creates a well-structured, engaging blog post.
    """)
    
    with st.form("blog_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            topic = st.text_input("Blog Topic *", placeholder="e.g., The Future of AI in Healthcare")
            target_audience = st.selectbox(
                "Target Audience",
                ["General Public", "Technical Professionals", "Business Leaders", "Students", "Researchers"]
            )
            tone = st.selectbox(
                "Tone",
                ["Professional", "Casual", "Academic", "Conversational", "Authoritative"]
            )
        
        with col2:
            word_count = st.slider("Target Word Count", 300, 2000, 800)
            include_images = st.checkbox("Include Image Suggestions", value=True)
            seo_focus = st.checkbox("SEO Optimized", value=True)
        
        # Image generation options
        if include_images:
            st.markdown("### 🎨 Image Generation Options")
            col3, col4 = st.columns(2)
            
            with col3:
                use_huggingface = st.checkbox("Use Free Hugging Face Models", value=True, help="Use free open-source models instead of paid services")
                if use_huggingface:
                    image_model = st.selectbox(
                    "Image Model",
                    ["FLUX.1-schnell (Fast)", "Stable Diffusion v1.5 (Classic)", "Stable Diffusion XL (High Quality)", "DreamShaper (Artistic)", "Openjourney (Creative)"],
                    help="Choose the AI model for image generation"
                )
            
            with col4:
                image_style = st.selectbox(
                    "Image Style",
                    ["Professional", "Artistic", "Modern", "Minimalist", "Realistic", "Abstract"],
                    help="Visual style for generated images"
                )
                image_quality = st.slider("Image Quality", 1, 10, 7, help="Higher values take longer but produce better images")
        
        additional_context = st.text_area(
            "Additional Context (Optional)",
            placeholder="Provide any specific points, research, or context you'd like included..."
        )
        
        submitted = st.form_submit_button("Generate Blog Post", type="primary")
    
    if submitted and topic:
        if not st.session_state.initialized:
            st.error("System not initialized. Please wait for initialization to complete.")
            return
        
        input_data = {
            "text": topic,
            "target_audience": target_audience,
            "tone": tone,
            "word_count": word_count,
            "include_images": include_images,
            "seo_focus": seo_focus,
            "additional_context": additional_context
        }
        
        # Add image generation options if images are enabled
        if include_images:
            input_data.update({
                "use_huggingface": use_huggingface,
                "image_style": image_style.lower(),
                "image_quality": image_quality
            })
            
            if use_huggingface:
                # Map display names to model enum values
                model_mapping = {
                    "FLUX.1-schnell (Fast)": "FLUX_SCHNELL",
                    "Stable Diffusion XL (High Quality)": "STABLE_DIFFUSION_XL",
                    "Stable Diffusion v1.5 (Classic)": "STABLE_DIFFUSION_V1_5",
                    "DreamShaper (Artistic)": "DREAMSHAPER",
                    "Openjourney (Creative)": "OPENJOURNEY"
                }
                input_data["image_model"] = model_mapping.get(image_model, "FLUX_SCHNELL")
        
        # Use the initialized bot from session state
        if 'agents' not in st.session_state or not st.session_state.agents:
            st.error("❌ ContentBot not properly initialized. Please refresh the page.")
            return
            
        # Create a temporary bot instance with the initialized agents
        bot = StreamlitContentBot()
        bot.agents = st.session_state.agents
        bot.db_manager = st.session_state.get('db_manager')
        
        with st.spinner("Generating blog post..."):
            result = bot.generate_content("blog", input_data)
        
        if result and result.get('success'):
            st.success("✅ Blog post generated successfully!")
            
            # Display the generated content
            content = result['content']
            state = result['state']
            
            st.markdown("## Generated Blog Post")
            
            # Title
            st.markdown(f"### {content.title}")
            
            # Metadata
            col1, col2 = st.columns(2)
            with col1:
                st.text(f"Sections: {len(content.sections)}")
            with col2:
                st.text(f"Keywords: {len(content.keywords)}")
            
            # Summary
            if content.summary:
                st.markdown("**Summary:**")
                st.info(content.summary)
            
            # Sections
            if content.sections:
                st.markdown("**Content Sections:**")
                for i, section in enumerate(content.sections, 1):
                    if 'heading' in section:
                        st.markdown(f"**{section['heading']}**")
                    if 'body' in section:
                        st.markdown(section['body'])
                    if i < len(content.sections):
                        st.markdown("---")
            
            # Keywords
            if content.keywords:
                st.markdown("**Keywords:**")
                st.write(", ".join(content.keywords))
            
            # Generated Images
            if state.image_content:
                if state.image_content.get('generated'):
                    st.markdown("**Generated Images:**")
                    
                    # Display main image
                    image_path = state.image_content.get('generated')
                    if isinstance(image_path, str):
                        try:
                            import os
                            if os.path.exists(image_path):
                                st.image(image_path, caption="Generated Image", use_column_width=True)
                            else:
                                st.error(f"❌ Image file not found: {image_path}")
                        except Exception as e:
                            st.error(f"❌ Could not display image: {str(e)}")
                            st.text(f"Image path: {image_path}")
                    
                    # Display image variants if available
                    if state.image_content.get('variants'):
                        st.markdown("**Image Variants:**")
                        cols = st.columns(min(3, len(state.image_content['variants'])))
                        for i, variant in enumerate(state.image_content['variants'][:3]):
                            with cols[i % 3]:
                                try:
                                    st.image(variant, caption=f"Variant {i+1}", use_column_width=True)
                                except Exception as e:
                                    st.warning(f"Could not display variant {i+1}: {str(e)}")
                                    st.text(f"Image URL: {variant}")
                    
                    # Show image generation details
                    with st.expander("🎨 Image Generation Details"):
                        if state.image_content.get('prompt_used'):
                            st.text(f"Prompt: {state.image_content['prompt_used']}")
                        if state.image_content.get('style'):
                            st.text(f"Style: {state.image_content['style']}")
                        if state.image_content.get('platform'):
                            st.text(f"Platform: {state.image_content['platform']}")
                        if state.image_content.get('model'):
                            st.text(f"Model: {state.image_content['model']}")
                        if state.image_content.get('generation_time'):
                            st.text(f"Generation time: {state.image_content['generation_time']:.2f}s")
                        if state.image_content.get('metadata'):
                            st.json(state.image_content['metadata'])
                
                elif state.image_content.get('error'):
                    st.error(f"❌ Image generation failed: {state.image_content['error']}")
                    
                    # Show attempted details even if generation failed
                    with st.expander("🎨 Image Generation Details"):
                        if state.image_content.get('prompt_used'):
                            st.text(f"Prompt: {state.image_content['prompt_used']}")
                        if state.image_content.get('style'):
                            st.text(f"Style: {state.image_content['style']}")
                        if state.image_content.get('platform'):
                            st.text(f"Platform: {state.image_content['platform']}")
                        st.text(f"Requirements: High quality, professional, relevant to the topic")
                        st.text(f"Style: modern")
                        st.text(f"Platform: {state.image_content.get('platform', 'twitter')}")
            
            # Analysis results
            if state.input_analysis:
                with st.expander("📊 Analysis Results"):
                    st.json(state.input_analysis)
    
    elif submitted and not topic:
        st.error("Please provide a blog topic.")


def render_social_media_generator():
    """Render the social media generator page."""
    st.markdown("# 📱 Social Media Content Generator")
    
    st.markdown("""
    Create engaging social media content optimized for different platforms.
    Each platform has specific requirements and best practices that the AI will follow.
    """)
    
    with st.form("social_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            message = st.text_area(
                "Message/Topic *",
                placeholder="What would you like to share? Describe your message or topic...",
                height=100
            )
            platform = st.selectbox(
                "Platform",
                ["twitter", "linkedin", "instagram", "facebook"]
            )
            content_type = st.selectbox(
                "Content Type",
                ["promotional", "educational", "entertaining", "news", "personal"]
            )
        
        with col2:
            include_hashtags = st.checkbox("Include Hashtags", value=True)
            include_emojis = st.checkbox("Include Emojis", value=True)
            call_to_action = st.checkbox("Include Call-to-Action", value=False)
            include_images = st.checkbox("Include Images", value=True)
        
        target_audience = st.text_input(
            "Target Audience (Optional)",
            placeholder="e.g., young professionals, tech enthusiasts, small business owners"
        )
        
        # Image generation options
        if include_images:
            st.markdown("### 🎨 Image Generation Options")
            col3, col4 = st.columns(2)
            
            with col3:
                use_huggingface = st.checkbox("Use Free Hugging Face Models", value=True, help="Use free open-source models instead of paid services")
                if use_huggingface:
                    image_model = st.selectbox(
                        "Image Model",
                        ["FLUX.1-schnell (Fast)", "Stable Diffusion v1.5 (Classic)", "Stable Diffusion XL (High Quality)", "DreamShaper (Artistic)", "Openjourney (Creative)"],
                        help="Choose the AI model for image generation"
                    )
            
            with col4:
                image_style = st.selectbox(
                    "Image Style",
                    ["Modern", "Artistic", "Professional", "Minimalist", "Realistic", "Abstract"],
                    help="Visual style for generated images"
                )
                image_quality = st.slider("Image Quality", 1, 10, 7, help="Higher values take longer but produce better images")
        
        submitted = st.form_submit_button("Generate Social Media Post", type="primary")
    
    if submitted and message:
        if not st.session_state.initialized:
            st.error("System not initialized. Please wait for initialization to complete.")
            return
        
        input_data = {
            "text": message,
            "platform": platform,
            "content_type": content_type,
            "include_hashtags": include_hashtags,
            "include_emojis": include_emojis,
            "call_to_action": call_to_action,
            "target_audience": target_audience,
            "include_images": include_images
        }
        
        # Add image generation options if images are enabled
        if include_images:
            input_data.update({
                "use_huggingface": use_huggingface,
                "image_style": image_style.lower(),
                "image_quality": image_quality
            })
            
            if use_huggingface:
                # Map display names to model enum values
                model_mapping = {
                    "FLUX.1-schnell (Fast)": "FLUX_SCHNELL",
                    "Stable Diffusion XL (High Quality)": "STABLE_DIFFUSION_XL",
                    "Stable Diffusion v1.5 (Classic)": "STABLE_DIFFUSION_V1_5",
                    "DreamShaper (Artistic)": "DREAMSHAPER",
                    "Openjourney (Creative)": "OPENJOURNEY"
                }
                input_data["image_model"] = model_mapping.get(image_model, "FLUX_SCHNELL")
        
        # Use the initialized bot from session state
        if 'agents' not in st.session_state or not st.session_state.agents:
            st.error("❌ ContentBot not properly initialized. Please refresh the page.")
            return
            
        # Create a temporary bot instance with the initialized agents
        bot = StreamlitContentBot()
        bot.agents = st.session_state.agents
        bot.db_manager = st.session_state.get('db_manager')
        
        with st.spinner("Generating social media post..."):
            result = bot.generate_content("social", input_data)
        
        if result and result.get('success'):
            st.success("✅ Social media post generated successfully!")
            
            # Display the generated content
            content = result['content']
            state = result['state']
            
            st.markdown("## Generated Social Media Post")
            
            # Platform info
            col1, col2 = st.columns(2)
            with col1:
                st.text(f"Platform: {content.platform.title()}")
            with col2:
                st.text(f"Characters: {len(content.content)}")
            
            # Content preview
            st.markdown("**Content:**")
            st.info(content.content)
            
            # Hashtags
            if content.hashtags:
                st.markdown("**Hashtags:**")
                hashtag_str = " ".join([f"#{tag}" for tag in content.hashtags])
                st.code(hashtag_str)
            
            # Platform-specific guidelines
            platform_limits = {
                "twitter": 280,
                "linkedin": 3000,
                "instagram": 2200,
                "facebook": 63206
            }
            
            char_count = len(content.content)
            limit = platform_limits.get(platform, 280)
            
            if char_count <= limit:
                st.success(f"✅ Within {platform.title()} character limit ({char_count}/{limit})")
            else:
                st.warning(f"⚠️ Exceeds {platform.title()} character limit ({char_count}/{limit})")
            
            # Generated Images
            if state.image_content:
                if state.image_content.get('generated'):
                    st.markdown("**Generated Images:**")
                    
                    # Display main image
                    image_path = state.image_content.get('generated')
                    if isinstance(image_path, str):
                        try:
                            import os
                            if os.path.exists(image_path):
                                st.image(image_path, caption="Generated Image", use_column_width=True)
                            else:
                                st.error(f"❌ Image file not found: {image_path}")
                        except Exception as e:
                            st.error(f"❌ Could not display image: {str(e)}")
                            st.text(f"Image path: {image_path}")
                    
                    # Display image variants if available
                    if state.image_content.get('variants'):
                        st.markdown("**Image Variants:**")
                        cols = st.columns(min(3, len(state.image_content['variants'])))
                        for i, variant in enumerate(state.image_content['variants'][:3]):
                            with cols[i % 3]:
                                try:
                                    st.image(variant, caption=f"Variant {i+1}", use_column_width=True)
                                except Exception as e:
                                    st.warning(f"Could not display variant {i+1}: {str(e)}")
                                    st.text(f"Image URL: {variant}")
                    
                    # Show image generation details
                    with st.expander("🎨 Image Generation Details"):
                        if state.image_content.get('prompt_used'):
                            st.text(f"Prompt: {state.image_content['prompt_used']}")
                        if state.image_content.get('style'):
                            st.text(f"Style: {state.image_content['style']}")
                        if state.image_content.get('platform'):
                            st.text(f"Platform: {state.image_content['platform']}")
                        if state.image_content.get('model'):
                            st.text(f"Model: {state.image_content['model']}")
                        if state.image_content.get('generation_time'):
                            st.text(f"Generation time: {state.image_content['generation_time']:.2f}s")
                        if state.image_content.get('metadata'):
                            st.json(state.image_content['metadata'])
                
                elif state.image_content.get('error'):
                    st.error(f"❌ Image generation failed: {state.image_content['error']}")
                    
                    # Show attempted details even if generation failed
                    with st.expander("🎨 Image Generation Details"):
                        if state.image_content.get('prompt_used'):
                            st.text(f"Prompt: {state.image_content['prompt_used']}")
                        if state.image_content.get('style'):
                            st.text(f"Style: {state.image_content['style']}")
                        if state.image_content.get('platform'):
                            st.text(f"Platform: {state.image_content['platform']}")
                        st.text(f"Requirements: High quality, professional, relevant to the topic")
                        st.text(f"Style: modern")
                        st.text(f"Platform: {state.image_content.get('platform', 'twitter')}")
            
            # Analysis results
            if state.input_analysis:
                with st.expander("📊 Analysis Results"):
                    st.json(state.input_analysis)
    
    elif submitted and not message:
        st.error("Please provide a message or topic.")


def render_monitoring_page():
    """Render the system monitoring page."""
    st.markdown("# 📊 System Monitoring")
    
    st.markdown("""
    Monitor the performance and health of the ContentBot system in real-time.
    """)
    
    # System health checks
    st.markdown("## 🏥 System Health")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state.initialized:
            st.success("✅ System Status: Online")
        else:
            st.error("❌ System Status: Offline")
    
    with col2:
        if st.session_state.db_connected:
            st.success("✅ Database: Connected")
        else:
            st.error("❌ Database: Disconnected")
    
    with col3:
        agent_count = len(st.session_state.agents) if st.session_state.agents else 0
        if agent_count > 0:
            st.success(f"✅ Agents: {agent_count} Active")
        else:
            st.warning("⚠️ Agents: None Loaded")
    
    # Agent details
    if st.session_state.agents:
        st.markdown("## 🤖 Agent Status")
        
        for agent_name, agent in st.session_state.agents.items():
            with st.expander(f"🔧 {agent_name.replace('_', ' ').title()}"):
                st.text(f"Type: {type(agent).__name__}")
                st.text(f"Status: Active")
                st.text(f"Module: {agent.__module__}")
    
    # Workflow statistics
    if st.session_state.workflow_history:
        st.markdown("## 📈 Workflow Statistics")
        
        # Calculate metrics
        total_workflows = len(st.session_state.workflow_history)
        successful_workflows = sum(1 for w in st.session_state.workflow_history if w.get('success', False))
        failed_workflows = total_workflows - successful_workflows
        success_rate = (successful_workflows / total_workflows) * 100 if total_workflows > 0 else 0
        
        # Content type breakdown
        content_types = {}
        for workflow in st.session_state.workflow_history:
            content_type = workflow.get('content_type', 'unknown')
            content_types[content_type] = content_types.get(content_type, 0) + 1
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Workflows", total_workflows)
        
        with col2:
            st.metric("Successful", successful_workflows, delta=None)
        
        with col3:
            st.metric("Failed", failed_workflows, delta=None)
        
        with col4:
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        # Content type chart
        if content_types:
            st.markdown("### Content Type Distribution")
            st.bar_chart(content_types)
        
        # Recent activity
        st.markdown("### Recent Activity")
        recent_workflows = sorted(
            st.session_state.workflow_history,
            key=lambda x: x['timestamp'],
            reverse=True
        )[:5]
        
        for workflow in recent_workflows:
            timestamp = workflow['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            content_type = workflow.get('content_type', 'unknown')
            success = workflow.get('success', False)
            status_icon = "✅" if success else "❌"
            
            st.text(f"{status_icon} {timestamp} - {content_type.title()} Content")


def render_history_page():
    """Render the workflow history page."""
    st.markdown("# 📋 Workflow History")
    
    st.markdown("""
    Review all previously generated content and workflow executions.
    """)
    
    if not st.session_state.workflow_history:
        st.info("No workflow history available. Generate some content to see it here!")
        return
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        content_type_filter = st.selectbox(
            "Filter by Content Type",
            ["All"] + list(set(w.get('content_type', 'unknown') for w in st.session_state.workflow_history))
        )
    
    with col2:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "Successful", "Failed"]
        )
    
    with col3:
        sort_order = st.selectbox(
            "Sort Order",
            ["Newest First", "Oldest First"]
        )
    
    # Apply filters
    filtered_workflows = st.session_state.workflow_history
    
    if content_type_filter != "All":
        filtered_workflows = [w for w in filtered_workflows if w.get('content_type') == content_type_filter]
    
    if status_filter == "Successful":
        filtered_workflows = [w for w in filtered_workflows if w.get('success', False)]
    elif status_filter == "Failed":
        filtered_workflows = [w for w in filtered_workflows if not w.get('success', False)]
    
    # Sort workflows
    reverse_sort = sort_order == "Newest First"
    filtered_workflows = sorted(filtered_workflows, key=lambda x: x['timestamp'], reverse=reverse_sort)
    
    # Display workflows
    for i, workflow in enumerate(filtered_workflows):
        timestamp = workflow['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        content_type = workflow.get('content_type', 'unknown')
        success = workflow.get('success', False)
        status_icon = "✅" if success else "❌"
        
        with st.expander(f"{status_icon} {timestamp} - {content_type.title()} Content"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Input Data:**")
                st.json(workflow.get('input_data', {}))
            
            with col2:
                if success and 'content' in workflow:
                    st.markdown("**Generated Content:**")
                    content = workflow['content']
                    
                    if hasattr(content, 'title'):
                        st.text(f"Title: {content.title}")
                    if hasattr(content, 'content'):
                        st.text_area("Content:", content.content, height=100, disabled=True)
                    if hasattr(content, 'tags') and content.tags:
                        st.text(f"Tags: {', '.join(content.tags)}")
                    if hasattr(content, 'hashtags') and content.hashtags:
                        st.text(f"Hashtags: {', '.join(content.hashtags)}")
                else:
                    st.markdown("**Error:**")
                    st.error(workflow.get('error', 'Unknown error occurred'))


def main():
    """Main application function."""
    # Initialize the system if not already done or if provider changed
    current_provider = getattr(st.session_state, 'llm_provider', 'gemini')
    agents_provider = getattr(st.session_state, 'agents_provider', None)
    
    if not st.session_state.initialized or agents_provider != current_provider:
        with st.spinner("Initializing ContentBot system..."):
            try:
                bot = StreamlitContentBot()
                success = asyncio.run(bot.initialize())
                
                if success:
                    # Store the bot instance in session state
                    st.session_state.bot = bot
                    st.success("✅ ContentBot initialized successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to initialize ContentBot. Please check the logs.")
                    return
                    
            except Exception as e:
                st.error(f"Failed to initialize the application: {str(e)}")
                return
    
    # Render sidebar and get selected page
    selected_page = render_sidebar()
    
    # Render the selected page
    if selected_page == "🏠 Home":
        render_home_page()
    elif selected_page == "📝 Blog Generator":
        render_blog_generator()
    elif selected_page == "📱 Social Media":
        render_social_media_generator()
    elif selected_page == "📊 Monitoring":
        render_monitoring_page()
    elif selected_page == "📋 History":
        render_history_page()


if __name__ == "__main__":
    main()