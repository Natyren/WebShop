"""
Test the site gym environment.

TODO: move to testing dir for more rigorous tests
"""
import gym
from rich import print
from rich.markup import escape

from web_agent_site.envs import WebAgentSiteEnv
from web_agent_site.models import (
    HumanPolicy,
    RandomPolicy,
)
from web_agent_site.utils import DEBUG_PROD_SIZE

import time
import base64
import os

from PIL import Image  # Ensure PIL is imported

if __name__ == '__main__':
    #env = gym.make('WebAgentSite-v0')
    env = WebAgentSiteEnv(render=True, pause=2.0)
    #env = WebAgentSiteEnv(observation_mode='html', render=False)
    #env = WebAgentSiteEnv(observation_mode='text', render=False, num_products=DEBUG_PROD_SIZE)
    global_step = 0

    # Create directory for resized images if it doesn't exist
    resized_dir = "resized_images"
    os.makedirs(resized_dir, exist_ok=True)
    
    try:
        #policy = HumanPolicy()
        _ = env.seed(42)
        env_seed = 0
        policy = RandomPolicy()
        info = env.reset()
        observation = env.observation
        i = 0
        
        while global_step < 40:
            i += 1
            # print(observation)
            available_actions = env.get_available_actions()
            print('Available actions:', available_actions)
            action = policy.forward(observation, available_actions)
            # print("action", action)
            print("action", action)
            observation, reward, done, info = env.step(action)

            # Resize and save the image
            img = observation.get("image", None)
            if img is not None and isinstance(img, Image.Image):
                w, h = img.size
                resized_img = img.resize((round(w / 2.5), round(h / 2.5)))
                img_filename = os.path.join(resized_dir, f"step_{global_step:04d}.png")
                resized_img.save(img_filename)
            
            print(observation.keys(), reward, done, info)
            print(f'{i}: Taking action "{escape(action)}" -> Reward = {reward}')
            print("")
            if done:
                env_seed += 1
                env.reset()
            global_step += 1
    finally:
        env.close()