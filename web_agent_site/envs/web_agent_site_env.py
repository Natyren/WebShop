import gym
import random
import requests
import string
import time
import io
import base64

from bs4 import BeautifulSoup
from bs4.element import Comment
from gym import spaces

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from web_agent_site.engine.engine import parse_action, END_BUTTON

from PIL import Image  # Added for PIL image wrapping

class WebAgentSiteEnv(gym.Env):
    """Gym environment for HTML mode of WebShop environment"""

    def __init__(self, observation_mode='html', **kwargs):
        """
        Constructor for HTML environment

        Arguments:
        observation_mode (`str`) -- ['html' | 'text'] (default 'html')
        pause (`float`) -- Pause (in seconds) after taking an action. 
            This is mainly for demo purposes.
            Recommended value: 2.0s
        render (`bool`) -- Show browser if set to `True`.
        session ('str') -- Session ID to initialize environment with
        """
        super(WebAgentSiteEnv, self).__init__()
        self.observation_mode = observation_mode
        self.kwargs = kwargs

        # Start Playwright and launch browser
        self._playwright = sync_playwright().start()
        headless = not kwargs.get('render', False)
        # launch_args = [
        #     '--no-sandbox',
        #     '--disable-setuid-sandbox',
        #     '--disable-dev-shm-usage',
        #     '--disable-web-security',
        #     '--disable-features=VizDisplayCompositor',
        #     '--disable-extensions',
        #     '--disable-plugins',
        #     '--disable-javascript',  # Disable JS if not needed for navigation
        #     '--disable-gpu',
        #     '--no-first-run',
        #     '--no-default-browser-check',
        #     '--disable-default-apps',
        #     '--disable-background-timer-throttling',
        #     '--disable-backgrounding-occluded-windows',
        #     '--disable-renderer-backgrounding',
        #     '--disable-ipc-flooding-protection',
        # ]
        self.browser = self._playwright.chromium.launch(headless=headless)#, args=launch_args)
        self.page = self.browser.new_page()
        # Set flags and values for WebShop session
        self.text_to_clickable = None
        self.assigned_session = kwargs.get('session')
        self.session = None
        self.reset()

    def step(self, action):
        """
        Takes an action, updates WebShop environment, and returns (observation, reward, done, info)

        Arguments:
        action (`str`): An action should be of the following structure:
          - search[keywords]
          - click[value]
        If action not valid, perform nothing.
        """
        reward = 0.0
        done = False
        info = None
        #print("action", action)
        action_name, action_arg = parse_action(action)
        if action_name == 'search':
            try:
                search_bar = self.page.query_selector("#search_input")
            except PlaywrightTimeoutError:
                search_bar = None
            if search_bar is not None:
                search_bar.fill(action_arg)
                search_bar.press("Enter")
        elif action_name == 'click':
            try:
                element = self.text_to_clickable[action_arg]
                try:
                    #print("element", element)
                    element.click(force=True)
                except Exception as e:
                    #print("error", e)
                    self.page.evaluate("el => el.click()", element, force=True)
            except Exception:
                pass
            reward = self.get_reward()
            if action_arg == END_BUTTON:
                done = True
        elif action_name == 'end':
            done = True
        else:
            print('Invalid action. No action performed.')

        if 'pause' in self.kwargs:
            time.sleep(self.kwargs['pause'])
        self.page.wait_for_load_state("networkidle")
        return self.observation, reward, done, info

    def get_available_actions(self):
        """Returns list of available actions at the current step"""
        # Determine if a search bar is available
        try:
            search_bar = self.page.query_selector("#search_input")
            has_search_bar = search_bar is not None
        except Exception:
            has_search_bar = False

        # Collect buttons, links, and options as clickables
        buttons = self.page.query_selector_all(".btn")
        product_links = self.page.query_selector_all(".product-link")
        buying_options = self.page.query_selector_all("input[type='radio']")

        self.text_to_clickable = {}
        for b in buttons + product_links:
            text = b.inner_text().strip()
            if text:
                self.text_to_clickable[text] = b
        for opt in buying_options:
            opt_value = opt.get_attribute('value')
            if opt_value:
                self.text_to_clickable[opt_value] = opt
        return dict(
            has_search_bar=has_search_bar,
            clickables=list(self.text_to_clickable.keys()),
        )

    def _parse_html(self, html=None, url=None):
        """
        Returns web request result wrapped in BeautifulSoup object

        Arguments:
        url (`str`): If no url or html is provided, use the current
            observation (HTML) for parsing.
        """
        if html is None:
            if url is not None:
                html = requests.get(url).text
            else:
                html = self.state['html']
        html_obj = BeautifulSoup(html, 'html.parser')
        return html_obj

    def get_reward(self):
        """Get reward value at current step of the environment"""
        html_obj = self._parse_html()
        r = html_obj.find(id='reward')
        r = float(r.findChildren("pre")[0].string) if r is not None else 0.0
        return r

    def get_instruction_text(self):
        """Get corresponding instruction text for environment current step"""
        html_obj = self._parse_html(self.page.content())
        instruction_text = html_obj.find(id='instruction-text').h4.text
        return instruction_text

    def convert_html_to_text(self, html):
        """Strip HTML of tags and add separators to convert observation into simple mode"""
        texts = self._parse_html(html).findAll(text=True)
        visible_texts = filter(tag_visible, texts)
        observation = ' [SEP] '.join(t.strip() for t in visible_texts if t != '\n')
        return observation

    def _get_rendered_image(self):
        """
        Capture a screenshot of the current browser page and return as a PIL Image.
        """
        # Playwright's screenshot returns bytes
        img_bytes = self.page.screenshot(full_page=True)
        img_pil = Image.open(io.BytesIO(img_bytes))
        return img_pil

    @property
    def state(self):
        """
        State that includes all information. The actual observation are
        likely to be a subset or reduced form of the state.
        """
        return dict(
            url=self.page.url,
            html=self.page.content(),
            instruction_text=self.instruction_text,
            image=self._get_rendered_image(),
        )

    @property
    def observation(self):
        """
        Compiles state into either the `html` or `text` observation mode,
        and always includes a rendered image from the browser as a PIL Image.
        Returns a dict with keys: 'observation', 'image'.
        """
        # html = self.state['html']
        image = self.state['image']
        # if self.observation_mode == 'html':
        #     obs = html
        # elif self.observation_mode == 'text':
        #     obs = self.convert_html_to_text(html)
        # else:
        #     raise ValueError(
        #         f'Observation mode {self.observation_mode} not supported.'
        #     )
        return {
            #'observation': obs,
            'image': image
        }

    @property
    def action_space(self):
        # Recommended to use `get_available_actions` instead
        return NotImplementedError

    @property
    def observation_space(self):
        return NotImplementedError

    def reset(self):
        """Create a new session and reset environment variables"""
        if self.assigned_session is not None:
            self.session = self.assigned_session
        else:
            self.session = ''.join(random.choices(string.ascii_lowercase, k=5))
        print(f'Session: {self.session}')
        init_url = f'http://127.0.0.1:3000/{self.session}'
        self.page.goto(init_url, wait_until="domcontentloaded")
        self.instruction_text = self.get_instruction_text()
        return self.observation, None

    def render(self, mode='human'):
        # TODO: Render observation in terminal or WebShop website
        return NotImplementedError

    def close(self):
        # TODO: When DB used instead of JSONs, tear down DB here
        self.page.close()
        self.browser.close()
        self._playwright.stop()
        print('Browser closed.')

def tag_visible(element):
    """Helper method to strip HTML block of extraneous tags"""
    ignore = {'style', 'script', 'head', 'title', 'meta', '[document]'}
    return (
        element.parent.name not in ignore and not isinstance(element, Comment)
    )
