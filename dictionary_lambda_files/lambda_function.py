############
# Julia McAnallen
# March 19, 2019
############
# This is a Dictionary Alexa Skill
# for English Language Learners
############
# Code modified from Amazon's sample
# lambda function for Color Picker
############

import logging
import requests
import re

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard

skill_name = "My Dictionary"
help_text = ("You can say: definition of word, example of word, or synonym of word.")

word_slot_key = "WORD"
example_slot_key = "EXAMPLE"
synonym_slot_key = "SYNONYM"
previous_key = "PREVIOUS"
# synonyms_list_key = "SYNONYMS"
word_slot = "word"
example_slot = "example"
synonym_slot = "synonym"

sb = SkillBuilder()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@sb.request_handler(can_handle_func=is_request_type("LaunchRequest"))
def launch_request_handler(handler_input):
    """Handler for Skill Launch."""
    # type: (HandlerInput) -> Response
    speech = "Welcome to the Merriam-Webster Dictionary. What word can I look up for you?"
    reprompt = "You can say: definition of word, example of word, or synonym of word."

    handler_input.response_builder.speak(speech).ask(reprompt)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.HelpIntent"))
def help_intent_handler(handler_input):
    """Handler for Help Intent."""
    # type: (HandlerInput) -> Response
    handler_input.response_builder.speak(help_text).ask(help_text)
    return handler_input.response_builder.response


@sb.request_handler(
    can_handle_func=lambda handler_input:
    is_intent_name("AMAZON.CancelIntent")(handler_input) or
    is_intent_name("AMAZON.StopIntent")(handler_input))
def cancel_and_stop_intent_handler(handler_input):
    """Single handler for Cancel and Stop Intent."""
    # type: (HandlerInput) -> Response
    speech_text = "Goodbye!"

    return handler_input.response_builder.speak(speech_text).response


@sb.request_handler(can_handle_func=is_request_type("SessionEndedRequest"))
def session_ended_request_handler(handler_input):
    """Handler for Session End."""
    # type: (HandlerInput) -> Response
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("WordDefinitionIntent"))
def my_word_definition_handler(handler_input):
    """
    Check if word is provided in slot values. Send word to URL-builder and
    return JSON data. Give user definition information.
    """
    # type: (HandlerInput) -> Response
    slots = handler_input.request_envelope.request.intent.slots

    if word_slot in slots:
        curr_word = slots[word_slot].value
        handler_input.attributes_manager.session_attributes[
            word_slot_key] = curr_word

        try:
            response = http_get(curr_word, False)

            if response:
                speech = ("The definition of {} with part of speech {} "
                          "is: {}".format(curr_word, response[0]['fl'], response[0]['shortdef'][0]))
                reprompt = ("What word would you like me to look up?")
            else:
                speech = ("I am sorry I could not find the word {}").format(curr_word)
                reprompt = ("What word would you like me to look up?")
        except:
            speech = ("I am sorry I could not find the word {}. "
                      "Can I look up another word?").format(curr_word)
            reprompt = ("What word would you like me to look up?")
    else:
        speech = "I'm not sure what word to look up, please try again"
        reprompt = ("I didn't catch that. What word would you like me "
                    "me to look up?")

    handler_input.attributes_manager.session_attributes[previous_key] = speech
    handler_input.response_builder.speak(speech).ask(reprompt)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("WordExampleIntent"))
def my_word_example_handler(handler_input):
    """
    This function handles the example sentence intent
    """
    # type: (HandlerInput) -> Response
    slots = handler_input.request_envelope.request.intent.slots

    if example_slot in slots:
        curr_word = slots[example_slot].value
        handler_input.attributes_manager.session_attributes[
            example_slot_key] = curr_word

        try:
            response = http_get(curr_word, False)

            if response:
                example = response[0]['def'][0]['sseq'][0][0][1]['dt'][1][0]
                if example == "vis":
                    vis = remove_italics(response[0]['def'][0]['sseq'][0][0][1]['dt'][1][1][0]['t'])
                    speech = ("An example with {} (part of speech {}) "
                              "is: {}".format(curr_word, response[0]['fl'],
                                              vis))
                elif example == "wsgram":
                    vis = remove_italics(response[0]['def'][0]['sseq'][0][0][1]['dt'][2][1][0]['t'])
                    speech = ("An example with {} (part of speech {}) "
                              "is: {}".format(curr_word, response[0]['fl'],
                                              vis))
                else:
                    speech = ("No example is available for {}").format(curr_word)
                reprompt = ("What word would you like me to look up?")
            else:
                speech = ("No example is available for {}").format(curr_word)
                reprompt = ("What word would you like me to look up?")
        except Exception as e:
            speech = ("No example is available for {}. "
                      "Can I look up another word?").format(curr_word)
            reprompt = ("What word would you like me to look up?")
    else:
        speech = "I'm not sure what word to look up, please try again"
        reprompt = ("I didn't catch that. What word would you like me "
                    "me to look up?")

    handler_input.attributes_manager.session_attributes[previous_key] = speech
    handler_input.response_builder.speak(speech).ask(reprompt)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("ThesaurusIntent"))
def my_word_example_handler(handler_input):
    """
    Look up word in thesaurus
    """
    # type: (HandlerInput) -> Response
    slots = handler_input.request_envelope.request.intent.slots

    if synonym_slot in slots:
        curr_word = slots[synonym_slot].value
        handler_input.attributes_manager.session_attributes[
            synonym_slot_key] = curr_word

        try:
            synonyms = http_get(curr_word, True)

            if type(synonyms[0]) == dict:
                speech = ("A synonym for {} is {}".format(curr_word,
                                                          synonyms[0]['meta']['syns'][0][0]))
                synonym_list = synonyms[0]['meta']['syns'][0]
                reprompt = ("What word would you like a synonym for?")
            else:
                speech = ("No synonyms for {} are available. "
                          "Can I look up another word?").format(curr_word)
                reprompt = ("What word would you like a synonym for?")
        except:
            speech = ("No synonyms for {} are available. "
                      "Can I look up another word?").format(curr_word)
            reprompt = ("What word would you like a synonym for?")
    else:
        speech = "I'm not sure what word to find a synonym for, please try again"
        reprompt = ("I didn't catch that. What word would you like me "
                    "me to look up a synonym for?")

    handler_input.attributes_manager.session_attributes[previous_key] = speech
    handler_input.response_builder.speak(speech).ask(reprompt)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.RepeatIntent"))
def repeat_handler(handler_input):
    speech = handler_input.attributes_manager.session_attributes[
        previous_key]
    reprompt = ("Would you like me to look up another word")
    handler_input.response_builder.speak(speech).ask(reprompt)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.FallbackIntent"))
def fallback_handler(handler_input):
    """AMAZON.FallbackIntent is only available in en-US locale.
    This handler will not be triggered except in that locale,
    so it is safe to deploy on any locale.
    """
    # type: (HandlerInput) -> Response
    speech = (
        "The {} skill can't help you with that. "
        "I can look up a word in the dictionary for you").format(skill_name)
    reprompt = ("I can look up a word in the dictionary, "
                "Just say any word in English")
    handler_input.response_builder.speak(speech).ask(reprompt)
    return handler_input.response_builder.response


def convert_speech_to_text(ssml_speech):
    """convert ssml speech to text, by removing html tags."""
    # type: (str) -> str
    s = SSMLStripper()
    s.feed(ssml_speech)
    return s.get_data()


@sb.global_response_interceptor()
def add_card(handler_input, response):
    """Add a card by translating ssml text to card content."""
    # type: (HandlerInput, Response) -> None
    response.card = SimpleCard(
        title=skill_name,
        content=convert_speech_to_text(response.output_speech.ssml))


@sb.global_response_interceptor()
def log_response(handler_input, response):
    """Log response from alexa service."""
    # type: (HandlerInput, Response) -> None
    print("Alexa Response: {}\n".format(response))


@sb.global_request_interceptor()
def log_request(handler_input):
    """Log request to alexa service."""
    # type: (HandlerInput) -> None
    print("Alexa Request: {}\n".format(handler_input.request_envelope.request))


@sb.exception_handler(can_handle_func=lambda i, e: True)
def all_exception_handler(handler_input, exception):
    """Catch all exception handler, log exception and
    respond with custom message.
    """
    # type: (HandlerInput, Exception) -> None
    print("Encountered following exception: {}".format(exception))

    speech = "That word is not in the dictionary. Please choose another word."
    handler_input.response_builder.speak(speech).ask(speech)

    return handler_input.response_builder.response


def http_get(curr_word, thesaurus):
    if thesaurus:
        base_url = "https://www.dictionaryapi.com/api/v3/references/ithesaurus/json/"
        key = "?key=7520b939-78bc-4060-b34c-61bd8765964c"
    else:
        base_url = "https://dictionaryapi.com/api/v3/references/learners/json/"
        key = "?key=56c632f1-bc5a-4123-b028-f238e027c1cf"
    url = base_url + curr_word + key
    response = requests.get(url=url)
    return response.json()


def remove_italics(text):
    return re.sub("{/?it}", "", text)


######## Convert SSML to Card text ############
# This is for automatic conversion of ssml to text content on simple card
# You can create your own simple cards for each response, if this is not
# what you want to use.

from six import PY2

try:
    from HTMLParser import HTMLParser
except ImportError:
    from html.parser import HTMLParser


class SSMLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.full_str_list = []
        if not PY2:
            self.strict = False
            self.convert_charrefs = True

    def handle_data(self, d):
        self.full_str_list.append(d)

    def get_data(self):
        return ''.join(self.full_str_list)


################################################


# Handler to be provided in lambda console.
lambda_handler = sb.lambda_handler()
