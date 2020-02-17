// DOM-Magic to avoid clicking links when forms have been changed.a

var changes = 0;

// Code for blocking unsaved forms

function formulon_initialize() {
    return;
    nodes = document.getElementsByTagName("a");
    form = document.forms[0];
    // don't destroy existing onClicks if no form is present!!
    if (form != undefined) {
        for (i=0;i<nodes.length;i++) {
            node = nodes.item(i);
            if (!node.hasAttribute("onClick")) {
                node.setAttribute("onClick", "verifyClick(this)");
            }
        }
    }
    focus_initialize();
}

function focus_initialize() {
    // get focus to most importent input field
    inputfields = document.getElementsByTagName("input");
    textareas = document.getElementsByTagName("textarea");
    var focus_node = undefined;
   
    for (i = 0; i < inputfields.length; i++) {
        inputfield = inputfields.item(i);
        if (inputfield.getAttribute("tabindex") == 1) {
            focus_node = inputfield;
            break;
        }
    }
    
    for (i = 0; i < textareas.length; i++) {
        if (focus_node != undefined) {
            break;
        }
        textarea = textareas.item(i);
        if (textarea.getAttribute("tabindex") == 1) {
            focus_node = textarea;
            break;
        }
    }
    
    if (focus_node == undefined) {
        focus_node = inputfields.item(0);
    }
    
    if (focus_node == undefined) {
        focus_node = textareas.item(0);
    }
    if (focus_node == undefined) {
        return;
    }
    focus_node.focus();
}

function reportChange(reference) {
    return;
    changes = 1;
    // Deactivate all links.
    nodes = document.getElementsByTagName("a");
    for (i=0;i<nodes.length;i++) {
        node = nodes.item(i);
        href = node.getAttribute("href");
        node.setAttributeNS("formulon", "href", href);
        node.removeAttribute("href");
    }
}

function resetForm(reference) {
    return;
    changes = 0;
    // Reactivate all links.
    nodes = document.getElementsByTagName("a");
    for (i=0;i<nodes.length;i++) {
        node = nodes.item(i);
        href = node.getAttributeNS("formulon","href");
        node.setAttribute("href", href);
    }
}

function verifyClick(reference) {
    return;
    if (changes == 0) {
        return;
    } else {
        if (confirm("Es wurden Daten bearbeitet. Um die Änderungen zu verwerfen drücken Sie bitte 'Ok'.")) {
        window.location.href = reference.getAttributeNS("formulon", "href");
        }
    }

// Code for menu switching

function switchMenu(name) {
    menu = document.getElementById(name+"_menu");
    add = document.getElementById(name+"_add");
    dummy = document.createElement("span");
    
    add_container = add.parentNode;
    menu_container = menu.parentNode;

    menu_container.insertBefore(dummy, menu)
    add_container.insertBefore(menu, add);
    menu_container.insertBefore(add, dummy)

    menu_container.removeChild(dummy);

    // Update the button text
    var text = "";
    if (menu.parentNode.getAttribute('id') == "hiddenContainer") {
        menu.setAttribute("disabled", "1");
        add.removeAttribute("disabled");
        text = "Auswahl";
    } else {
        add.setAttribute("disabled", "1");
        menu.removeAttribute("disabled");
        text = "Neu";
    }
    button = document.getElementById(name+"_button")
    button.removeChild(button.firstChild);
    span = document.createElement("span");
    span.appendChild(document.createTextNode(text));
    button.appendChild(span);
}

}


