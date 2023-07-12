# Author: Radiance O. Ngonnase

# All references used are listed in the REFERENCES document
# submitted along with the project folder.

##### START #####

import databutton as db

import streamlit as st
import streamlit.components.v1 as components
from streamlit_chat_media import message

import openai

import torch

from transformers import pipeline
import accelerate

import io
from PIL import Image

st.set_page_config(page_title="StyleBot", page_icon="🤖", layout="wide")

# Store the messages between the bot and the user in the session state:

# The current message the user has sent
if "user_message" not in st.session_state:
    st.session_state["user_message"] = ""

# A list of all messages received from the user
if "received_messages" not in st.session_state:
    st.session_state["received_messages"] = []

# A list of all messages sent by the bot to the user
if "sent_messages" not in st.session_state:
    st.session_state["sent_messages"] = []

# A kind of "short-term" memory for the bot,
# used in calls to the ChatGPT API
if "memory" not in st.session_state:
    # Set the context/role/instructions/background information for ChatGPT
    st.session_state["memory"] = [
        {
            "role": "system",
            "content": "Your name is StyleBot, you are a personalized fashion assistant, advisor "
            + "and stylist. You provide advice based on the user's gender, description of what they look"
            + "like or from uploaded images that show this, in addition to other information they provide. "
            + "Try to include one or more fashion-related emojis when introducing yourself. Keep your "
            + "introduction VERY BRIEF. When giving recommendations much later during the conversation, don't "
            + "forget to include your reasons for suggesting each fashion item. Images of each item will also "
            + "be generated for you. To help with this, also include a separate name for each item, "
            + "enclosed in it's own square brackets, at the end of your response. DO NOT include external "
            + "hyperlinks in your response. Also, DO NOT include descriptions for emojis in your response. "
            + "If necessary, let the user know that they can upload images by clicking on the picture icon "
            + "in the input field and uploading an image file.",
        }
    ]


########################## FUNCTION DEFINITIONS #########################
################# All helper functions are defined first. ###############

## User input ##


# Helper
def add_style():
    """
    Adds CSS styling information for the app UI.
    """
    css_style = """
        <style> 
            [data-testid=stVerticalBlock], .e1tzin5v0 /* div that contains all the messages */ {
                position: fixed;
                top: 55px;
                bottom: 65px;
                overflow: auto;
                padding-right: 10px;
                max-height: 100%;
                min-width: 90%;
                max-width: 100%;
                margin-left: auto;
                margin-right: auto;
            }

            /* For all divs that contain a message */
            .element-container  {
                position: relative;
                bottom: -20px;
            }

            /** 
             * Position text field for getting user input and
             * the send button image at the bottom of the page.
             */

            .stTextInput, div[data-testid="stImage"], img, .stButton {
                position: fixed;
            }

            .stTextInput {
                bottom: 10px;
            }

            .stTextInput input {
                width: 93%;
            }

            /* Buttons */
            div[data-testid="stImage"], img {
                right: 10px;
                bottom: 7.5px;
            }

            /* Box that contains info/help text for the input field */
            .css-1li7dat {
                left: 7px;
                bottom: 0.5px;
                font-size: 8px;
                text-align: center;
            }

            /* Remove the expand button of the button images */
            button[title="View fullscreen"], .e19lei0e0  {
                display: none;
            }

            /* File uploader. (Also, hide it by default */

            div[data-testid="stFileUploader"], .exg6vvm0  {
                position: fixed;
                top: 50px;
                min-width: 85%;
                display: none;
            }

            .exg6vvm15 {
                height: 70vh;
            }

            /* Remove the footer */
            footer {
                display: none;
            }
        </style>
    """
    st.markdown(css_style, unsafe_allow_html=True)


# Helper
def add_buttons():
    """
    Adds a 'Send' button to the text input box,
    denoted by a forward pointing arrow. Also adds
    a button for uploading images, denoted by a
    picture icon.
    """
    if st.session_state.added_buttons == False:
        send_button_img = db.storage.binary.get(key="send-button-icon-png")
        st.image(send_button_img, width=25, output_format="PNG")

        picture_icon_img = db.storage.binary.get(key="picture-icon-png")
        st.image(picture_icon_img, width=25, output_format="PNG")

        javascript_code = """
            <script type="text/javascript">

                /*
                * Position the send button in the input box
                * and its functionality to it. Do the same for
                * the picture icon that serves as a button that
                * allows the user to upload images.
                */
            
                function addButtons() {
                    let textInput = window.parent.document.querySelector(".stTextInput");
                    let buttons = window.parent.document.querySelectorAll(".etr89bj1");
                
                    for (let i = 0; i < 2; i++) {

                        try {
                            image = buttons[i].querySelector("img");
                            textInput.appendChild(image);
                            image.style.position = "absolute";
                            buttons[i].remove();
                        }
                        catch(err) {
                            image = textInput.querySelector("img");
                        }

                        if (i == 0) {
                            let sendButton = image
                            sendButton.addEventListener("click", () => {
                                textInput.dispatchEvent("change", {bubbles: false});
                            });
                        }
                        else if (i == 1) {
                            var rightMargin = 50;
                            image.style.right = rightMargin.toString() + "px";

                            let pictureButton = image;
                            pictureButton.addEventListener("click", () => {
                                // Make the file uploader visible
                                let uploader = window.parent.document.querySelector(".exg6vvm0");
                                uploader.style.display = "block";
                                
                            });
                        }
                        
                    }
                    
                }

                setTimeout(addButtons, 1500);

            </script>
        """
        components.html(javascript_code, height=0)

        st.session_state.added_buttons = True


# MAJOR
def get_user_input():
    """
    Get and display the user's message.
    """
    # Add a file uploader for uploading images to the page
    add_file_uploader()

    # Add an input text box to the page
    st.text_input(
        label="Enter a message: ",
        label_visibility="collapsed",
        key="user_message",
        on_change=display_prompt_and_response(),
        placeholder="Tell me something...",
    )

    # Add some styling information
    add_style()

    # Add buttons to the input box
    if "added_buttons" not in st.session_state:
        st.session_state.added_buttons = False
    st.session_state.added_buttons = False
    add_buttons()


## Show messages ##


def add_file_uploader():
    """
    Add a file uploader that allows the user to upload images
    of themselves to inform StyleBot's recommendations.
    """
    if "file_container" not in st.session_state:
        st.session_state.file_container = st.empty()

    with st.session_state.file_container:
        uploaded_image = st.file_uploader(
            label="Upload an image of yourself: ", label_visibility="collapsed"
        )

        if uploaded_image is not None:
            image = Image.open(io.BytesIO(uploaded_image.getvalue()))

            # Generate a text description from the user's uploaded image
            # using one of the transformer models for Hugging Face's Image-To-Text Pipeline
            captioner = pipeline(
                task="image-to-text", model="Salesforce/blip-image-captioning-base"
            )
            st.session_state.user_message = captioner(image)[0]["generated_text"]


def remove_buttons():
    javascript_code = """
        <script type="text/javascript">

            function removeButtons() {
                // Delete buttons to add them back again later (prevents display error on re-render)
                let textInput = window.parent.document.querySelector(".stTextInput");
                buttons = textInput.querySelectorAll("img");

                for(let i = 0; i < buttons.length; i++) {
                    buttons[i].remove();
                }

            }

            setTimeout(removeButtons, 2000);

        </script>
    """
    components.html(javascript_code, height=0)


# Helper
def formulate_response():
    """
    Generates the contents of the bot's messages.
    (When talking to the user, these are equivalent
    to the bot's responses to the user's inputs)
    """
    openai.api_key = db.secrets.get("OpenAI_API_Key")

    my_response = ""

    my_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=st.session_state.memory
    )

    my_response = my_response["choices"][0]["message"]["content"]

    return my_response


# Helper
def update_memory(role, message):
    """
    Adds a message to the bot's memory of the conversation.
    """
    if len(st.session_state.memory) > 4:
        st.session_state.memory.pop(1)

    message = {"role": role, "content": message}

    if message not in st.session_state.memory:
        st.session_state.memory.append(message)


# Helper
def get_bot_response():
    """
    Retrieves the next message to be sent by the bot.
    """
    # Use ChatGPT to create a response
    my_response = formulate_response()
    if my_response:
        st.session_state["sent_messages"].append(my_response)
        update_memory("assistant", my_response)


# Helper
def generate_image(img_description):
    """
    Generates an image of a fashion item, using the DALL-E API.
    """
    result = openai.Image.create(prompt=img_description, n=1, size="256x256")
    img_src = result["data"][0]["url"]

    return img_src


# Helper
def generate_item_images(msg_index):
    """
    Generates images for any recommended fashion items
    mentioned in the bot's response to the user. In the
    bot's message, any image descriptions are enclosed in
    square brackets and that is what is used for image generation.
    """
    bot_message = st.session_state["sent_messages"][msg_index]

    if bot_message.find("[") >= 0:
        if "images" + str(msg_index) not in st.session_state:
            st.session_state["images" + str(msg_index)] = []

            image_count = 1

            while bot_message.find("[") >= 0 and image_count <= 5:
                index1 = bot_message.find("[")
                index2 = bot_message.find("]")

                img_description = bot_message[(index1 + 1) : index2]

                st.session_state["images" + str(msg_index)].append(
                    [generate_image(img_description), img_description]
                )

                bot_message = bot_message.replace(str(img_description), " ")
                bot_message = bot_message.replace("[ ]", " ")

                image_count = image_count + 1

            st.session_state["sent_messages"][msg_index] = bot_message


# Helper
def display_messages():
    """
    Displays the messages exchanged during the chat conversation.
    """
    # Display messages from the user
    if st.session_state["received_messages"]:
        for i in range(len(st.session_state["received_messages"])):
            message(
                st.session_state["received_messages"][i],
                is_user=True,
                key="received" + str(i),
            )

            # Display messages from the bot in response to the suer
            if st.session_state["sent_messages"]:
                if i < (len(st.session_state["sent_messages"])):
                    # Generate images for recommended fashion items in the message if any
                    # and modify the message with image descriptions removed
                    generate_item_images(i)

                    # Display the bot's message
                    message(
                        st.session_state["sent_messages"][i],
                        key="sent" + str(i),
                    )

                    # and any generated images too
                    if "images" + str(i) in st.session_state:
                        count = 1
                        for image in st.session_state["images" + str(i)]:
                            message(
                                image[0],
                                key="sent" + str(i) + "image" + str(count),
                            )
                            message(
                                image[1], key="sent" + str(i) + "img_descr" + str(count)
                            )
                            count = count + 1

        return True

    return False


# Helper
def get_prompt_and_response():
    """
    Retrieves both the last message received
    from the user and StyleBot's response to it.
    """
    # If the user has actually typed in a message
    if st.session_state["user_message"]:
        # Add it to the list of messages the bot has received
        # and update the messages prompt to the ChatGPT API
        new_user_message = st.session_state["user_message"]
        st.session_state["received_messages"].append(new_user_message)
        update_memory("user", new_user_message)

        # Delete the cached value of the text input field
        # to prevent duplicate messages, in the case of page reload
        del st.session_state["user_message"]

        # Clear the text box for the user
        st.session_state["user_message"] = ""

        # Get StyleBot's response to the user
        get_bot_response()


# Helper
def autoscroll_and_format():
    """
    Add some interactivity and do some extra formatting for
    the appearance of the app's UI when a message is displayed
    (or processed in the case of images).
    """

    remove_buttons()

    javascript_code = """
            <script type="text/javascript">
        
                window.parent.document.onload = (() => {

                    /* Auto-scrolling */

                    // Retrieve the vertical block/container
                    const messagesBlock = window.parent.document.querySelector("[data-testid=stVerticalBlock]");

                    // Scroll down continuously (every millisecond)
                    const autoScroll = setInterval(function(messagesBlock) {
                        messagesBlock.scrollTop = messagesBlock.scrollHeight;
                    }, 1, messagesBlock);

                    // Stop when the bottom of the block is reached (after one second has passed)
                    const stopScroll = setTimeout(function() {
                        clearInterval(autoScroll);
                    }, 2000);

                    
                    /* 
                    * Hide all containers that contain Javascript and/or CSS code (including this one) 
                    * to prevent the addition of extra spacing under the last displayed message.
                    */

                    function hide(containers) {
                        for (let container of containers) {
                            container.parentElement.style.display = "none";
                        }
                    }

                    var containers = window.parent.document.querySelectorAll(".element-container iframe[title='st.iframe']");
                    hide(containers);

                    containers = window.parent.document.querySelectorAll(".element-container .stMarkdown");
                    hide(containers);

                    /* 
                    * Allow wrapping of long words in each message box 
                    */

                    var messageBoxes = window.parent.document.querySelectorAll(".element-container iframe[title='streamlit_chat_media.streamlit_chat_media']");
                    if (messageBoxes) {
                        for (let box of messageBoxes) {
                            console.log(box);
                            console.log(box.contentDocument);
                            box.contentDocument.body.style.wordWrap = "break-word";
                            setInterval(() => {
                                if (box.contentDocument.querySelector("a") != null) {
                                    box.setAttribute("width", "400");
                                    box.setAttribute("height", "230");
                                    var imageLink = box.contentDocument.getElementsByTagName("a")[0];
                                    console.log(imageLink);
                                    var image = box.contentDocument.createElement("img");
                                    console.log(image);
                                    image.setAttribute("src", imageLink.getAttribute("href"));
                                    image.setAttribute("width", "200");
                                    image.setAttribute("height", "200");
                                    
                                    console.log(imageLink.parentElement.replaceChild(image, imageLink));
                                }
                            }, 3000);
                        }
                    }
                })();
                    
            </script>
        """
    components.html(javascript_code, height=0)

    st.session_state.added_buttons = False
    add_buttons()


# MAJOR
def display_prompt_and_response():
    """
    Shows the last message received from the user
    and the corresponding response from StyleBot.
    """
    # Get the last message received from the user and StyleBot's response
    get_prompt_and_response()

    # Display all messages received so far,
    # including the messages retrieved above
    if display_messages():
        # Automatically scroll down to make the last displayed message
        # visible and do some additional formatting for UI appearance
        autoscroll_and_format()


# Utility function
def send_messages(batch_name, message_list):
    """
    For sending a batch of messages to the user.
    """
    for bot_message in message_list:
        # Show each message
        message(bot_message, key=batch_name + str(message_list.index(bot_message) + 1))

        # and add it to the bot's memory
        update_memory("assistant", bot_message)


## Main function (creates the app) ##


def main():
    # Start the conversation #

    # Introduction message
    if "intro1" not in st.session_state:
        st.session_state["intro1"] = formulate_response()

    # Keep track of the originally generated message during page reload
    intro_message = st.session_state["intro1"]

    send_messages("intro", [intro_message])

    get_user_input()


if __name__ == "__main__":
    main()
