import xml.etree.ElementTree as ET

# Mapping of custom tags to HTML equivalents
tag_mapping = {
    "notification": "div",
    "panel": "div",
    "text": "span",
    "progress_bar": "progress",
    "input": "input",
    "checkbox": "input",
    "button": "button",
    "image": "img",
    "dropdown": "select",
    "list": "ul",
    "list_item": "li",
    "date_picker": "input",
    "file_upload": "input",
    "radio": "input",
}


# Attributes handling
def handle_attributes(element):
    attrib = element.attrib
    html_attrib = {"class": "dark-theme"}

    # Handle each specific case of conversion
    if element.tag == "notification":
        html_attrib["class"] = "notification dark-theme"
        html_attrib["title"] = attrib.get("title", "")
        for key, value in attrib.items():
            if key != "title":
                html_attrib[key] = value
    elif element.tag == "panel":
        html_attrib["class"] = "panel dark-theme"
        html_attrib["title"] = attrib.get("title", "")
        for key, value in attrib.items():
            if key != "title":
                html_attrib[key] = value
    elif element.tag == "progress_bar":
        html_attrib["max"] = attrib.get("total", "100")
        html_attrib["value"] = attrib.get("done", "0")
        for key, value in attrib.items():
            if key not in ["total", "done"]:
                html_attrib[key] = value
    elif element.tag == "input":
        html_attrib["type"] = attrib.get("type", "text")
        if "value" in attrib:
            html_attrib["value"] = attrib.get("value", "")
        if "placeholder" in attrib:
            html_attrib["placeholder"] = attrib["placeholder"]
        for key, value in attrib.items():
            if key not in ["type", "value", "placeholder"]:
                html_attrib[key] = value
    elif element.tag == "checkbox":
        html_attrib["type"] = "checkbox"
        if attrib.get("checked", "false") == "true":
            html_attrib["checked"] = "checked"
        for key, value in attrib.items():
            if key != "checked":
                html_attrib[key] = value
    elif element.tag == "dropdown":
        pass  # Handled separately for <dropdown>
    elif element.tag == "image":
        html_attrib["src"] = attrib.get("src", "")
        html_attrib["alt"] = attrib.get("alt", "")
        for key, value in attrib.items():
            if key not in ["src", "alt"]:
                html_attrib[key] = value
    elif element.tag == "date_picker":
        html_attrib["type"] = "date"
        html_attrib["value"] = attrib.get("value", "")
        for key, value in attrib.items():
            if key != "value":
                html_attrib[key] = value
    elif element.tag == "file_upload":
        html_attrib["type"] = "file"
        if attrib.get("multiple", "false") == "true":
            html_attrib["multiple"] = "multiple"
        for key, value in attrib.items():
            if key != "multiple":
                html_attrib[key] = value
    elif element.tag == "radio":
        html_attrib["type"] = "radio"
        html_attrib["name"] = attrib.get("name", "")
        html_attrib["value"] = attrib.get("value", "")
        if attrib.get("checked", "false") == "true":
            html_attrib["checked"] = "checked"
        for key, value in attrib.items():
            if key not in ["name", "value", "checked"]:
                html_attrib[key] = value
    elif element.tag == "button":
        if "onclick" in attrib:
            html_attrib["onclick"] = attrib.get("onclick", "")
        else:
            html_attrib["onclick"] = "alert('Button clicked!')"
        for key, value in attrib.items():
            if key != "onclick":
                html_attrib[key] = value
    else:
        # Handle generic attributes
        for key, value in attrib.items():
            html_attrib[key] = value
    return html_attrib


# Recursive function to convert the XML-like structure to HTML
def convert_to_html(element):
    tag = element.tag
    html_tag = tag_mapping.get(tag, "tag")

    # Handle special cases
    if tag == "dropdown":
        # Create a <select> element
        html_str = f'<{html_tag} class="dark-theme">'
        options = element.attrib.get("options", "").split(",")
        selected = element.attrib.get("selected", "")
        for option in options:
            if option.strip() == selected:
                html_str += (
                    f'<option selected class="dark-theme">{option.strip()}</option>'
                )
            else:
                html_str += f'<option class="dark-theme">{option.strip()}</option>'
        html_str += f"</{html_tag}>"
    elif tag == "panel":
        html_str = f'<div class="panel dark-theme">'
        title = element.attrib.get("title")
        if title:
            html_str += f"<span>{title}</span>"
        html_str += '<div class="panel dark-theme">'
        for child in element:
            html_str += convert_to_html(child)
        html_str += "</div>"
        html_str += f"</div>"
    elif tag == "br":
        html_str = "<br/>"
    elif tag == "hr":
        html_str = "<hr/>"
    else:
        # Convert the remaining elements normally
        attribs = handle_attributes(element)
        attrib_str = " ".join([f'{key}="{value}"' for key, value in attribs.items()])
        if attrib_str:
            html_str = f"<{html_tag} {attrib_str}>"
        else:
            html_str = f"<{html_tag}>"

        # If element has text, include it
        if element.text:
            html_str += element.text

        # Recursively convert children
        for child in element:
            html_str += convert_to_html(child)

        # Close the tag
        html_str += f"</{html_tag}>"

    return html_str


# Function to parse the custom XML and convert it to HTML with CSS
def parse_custom_gui(xml_string):
    root = ET.fromstring(xml_string)
    html_content = convert_to_html(root)
    return f'<div class="dark-theme">{html_content}</div>'


if __name__ == "__main__":
    xml_input = """
    <gui>
        <notification title="New Message">
            You received a new notification!
        </notification>
        <panel title="User Info">
            <text>Hello, User!</text>
        </panel>
        
        <progress_bar total="100" done="70"/>
        <input type="text" value="John Doe"/>
        <text> Accept Terms: </text><checkbox checked="true"/>
        <button>Submit</button>
        
        <image src="https://example.com/image.png" alt="Example Image"/>
        
        <dropdown options="Option 1, Option 2, Option 3" selected="Option 2"/>
        
        <list>
            <list_item>Item 1</list_item>
            <list_item>Item 2</list_item>
            <list_item>Item 3</list_item>
        </list>
        
        <date_picker value="2024-01-01"/>
        <file_upload multiple="true"/>
        
        <text>Option A: </text><radio name="group1" value="A" checked="true"/>
        <text>Option B: </text><radio name="group1" value="B"/>
    </gui>
    """

    html_output = parse_custom_gui(xml_input)
    with open("temp.html", "w") as f:
        f.write(html_output)
