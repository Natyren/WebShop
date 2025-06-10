#!/usr/bin/env python3
"""
Test script to validate WebShop environment performance improvements
"""

import time
from web_agent_site.envs.web_agent_site_env import WebAgentSiteEnv
from start_webshop_server import WebShopServerManager

def test_environment_speed():
    """Test the environment with different configurations."""
    
    # Start server manager
    server_manager = WebShopServerManager()
    
    print("🚀 Starting WebShop server...")
    if not server_manager.start_server():
        print("❌ Could not start server. Please start it manually.")
        return
    
    try:
        # Test configurations
        configs = [
            {"name": "Fast Mode (Recommended)", "fast_mode": True, "render": False},
            {"name": "Standard Mode", "fast_mode": False, "render": False},
            {"name": "Debug Mode (with browser)", "fast_mode": True, "render": True, "pause": 1.0},
        ]
        
        for config in configs:
            print(f"\n{'='*60}")
            print(f"Testing: {config['name']}")
            print(f"{'='*60}")
            
            config_params = config.copy()
            config_params.pop('name')
            
            # Time the initialization
            start_time = time.time()
            
            try:
                env = WebAgentSiteEnv(**config_params)
                init_time = time.time() - start_time
                print(f"✅ Environment initialized in {init_time:.2f} seconds")
                
                # Test a few actions
                start_time = time.time()
                
                # Search action
                obs, reward, done, info = env.step("search[laptop]")
                search_time = time.time() - start_time
                print(f"✅ Search action completed in {search_time:.2f} seconds")
                
                # Get available actions
                start_time = time.time()
                actions = env.get_available_actions()
                action_time = time.time() - start_time
                print(f"✅ Got available actions in {action_time:.2f} seconds")
                print(f"   Found {len(actions.get('clickables', []))} clickable elements")
                
                # Test click action if available
                if actions.get('clickables'):
                    start_time = time.time()
                    first_clickable = actions['clickables'][0]
                    obs, reward, done, info = env.step(f"click[{first_clickable}]")
                    click_time = time.time() - start_time
                    print(f"✅ Click action completed in {click_time:.2f} seconds")
                
                env.close()
                print(f"✅ Test completed successfully for {config['name']}")
                
            except Exception as e:
                print(f"❌ Error testing {config['name']}: {e}")
                continue
        
        print(f"\n{'='*60}")
        print("🎉 All tests completed!")
        print(f"{'='*60}")
        
    finally:
        # Clean up server
        server_manager.stop_server()

def performance_tips():
    """Print performance optimization tips."""
    print("""
🚀 WebShop Performance Optimization Tips:

1. **Use Fast Mode (Default)**:
   env = WebAgentSiteEnv(fast_mode=True)
   
2. **Disable Rendering for Training**:
   env = WebAgentSiteEnv(render=False)
   
3. **Reduce Pause Time**:
   env = WebAgentSiteEnv(pause=0.1)  # or remove pause entirely
   
4. **Pre-start the Server**:
   python start_webshop_server.py --action start
   
5. **Use Headless Mode**:
   env = WebAgentSiteEnv(render=False)  # Default behavior
   
6. **Monitor Server Performance**:
   python start_webshop_server.py --action status

Key Improvements Made:
✅ Added browser launch optimizations (--no-sandbox, --disable-images, etc.)
✅ Implemented connection retry logic with exponential backoff
✅ Added server health checks before navigation
✅ Optimized timeout settings for different modes
✅ Disabled unnecessary resource loading (images, CSS, JS in fast mode)
✅ Added fast vs standard mode options
✅ Improved error handling and diagnostics
""")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Test WebShop Environment Performance')
    parser.add_argument('--test', action='store_true', help='Run performance tests')
    parser.add_argument('--tips', action='store_true', help='Show performance tips')
    
    args = parser.parse_args()
    
    if args.test:
        test_environment_speed()
    elif args.tips:
        performance_tips()
    else:
        print("Use --test to run performance tests or --tips to see optimization advice")
        performance_tips() 