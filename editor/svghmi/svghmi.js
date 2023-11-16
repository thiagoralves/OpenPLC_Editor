// svghmi.js

function dispatch_value(index, value) {
    let widgets = subscribers(index);

    let oldval = cache[index];
    cache[index] = value;

    if(widgets.size > 0) {
        for(let widget of widgets){
            widget.new_hmi_value(index, value, oldval);
        }
    }
};

function init_widgets() {
    Object.keys(hmi_widgets).forEach(function(id) {
        let widget = hmi_widgets[id];
        widget.do_init();
    });
};

// Open WebSocket to relative "/ws" address
var has_watchdog = window.location.hash == "#watchdog";

const dvgetters = {
    SINT:  (dv,offset) => [dv.getInt8(offset, true), 1],
    INT:   (dv,offset) => [dv.getInt16(offset, true), 2],
    DINT:  (dv,offset) => [dv.getInt32(offset, true), 4],
    LINT:  (dv,offset) => [dv.getBigInt64(offset, true), 8],
    USINT: (dv,offset) => [dv.getUint8(offset, true), 1],
    UINT:  (dv,offset) => [dv.getUint16(offset, true), 2],
    UDINT: (dv,offset) => [dv.getUint32(offset, true), 4],
    ULINT: (dv,offset) => [dv.getBigUint64(offset, true), 8],
    BOOL:  (dv,offset) => [dv.getInt8(offset, true), 1],
    NODE:  (dv,offset) => [dv.getInt8(offset, true), 1],
    REAL:  (dv,offset) => [dv.getFloat32(offset, true), 4],
    STRING: (dv, offset) => {
        const size = dv.getInt8(offset);
        return [
            String.fromCharCode.apply(null, new Uint8Array(
                dv.buffer, /* original buffer */
                offset + 1, /* string starts after size*/
                size /* size of string */
            )), size + 1]; /* total increment */
    }
};

// Called on requestAnimationFrame, modifies DOM
var requestAnimationFrameID = null;
function animate() {
    let rearm = true;
    do{
        if(page_fading == "pending" || page_fading == "forced"){
            if(page_fading == "pending")
                svg_root.classList.add("fade-out-page");
            page_fading = "in_progress";
            if(page_fading_args.length)
                setTimeout(function(){
                    switch_page(...page_fading_args);
                },1);
            break;
        }

        // Do the page swith if pending
        if(page_switch_in_progress){
            if(current_subscribed_page != current_visible_page){
                switch_visible_page(current_subscribed_page);
            }

            page_switch_in_progress = false;

            if(page_fading == "in_progress"){
                svg_root.classList.remove("fade-out-page");
                page_fading = "off";
            }
        }

        if(jumps_need_update) update_jumps();


        pending_widget_animates.forEach(widget => widget._animate());
        pending_widget_animates = [];
        rearm = false;
    } while(0);

    requestAnimationFrameID = null;

    if(rearm) requestHMIAnimation();
}

function requestHMIAnimation() {
    if(requestAnimationFrameID == null){
        requestAnimationFrameID = window.requestAnimationFrame(animate);
    }
}

// Message reception handler
// Hash is verified and HMI values updates resulting from binary parsing
// are stored until browser can compute next frame, DOM is left untouched
function ws_onmessage(evt) {

    let data = evt.data;
    let dv = new DataView(data);
    let i = 0;
    try {
        for(let hash_int of hmi_hash) {
            if(hash_int != dv.getUint8(i)){
                throw new Error("Hash doesn't match");
            };
            i++;
        };

        while(i < data.byteLength){
            let index = dv.getUint32(i, true);
            i += 4;
            let iectype = hmitree_types[index];
            if(iectype != undefined){
                let dvgetter = dvgetters[iectype];
                let [value, bytesize] = dvgetter(dv,i);
                dispatch_value(index, value);
                i += bytesize;
            } else {
                throw new Error("Unknown index "+index);
            }
        };

        // register for rendering on next frame, since there are updates
    } catch(err) {
        // 1003 is for "Unsupported Data"
        // ws.close(1003, err.message);

        // TODO : remove debug alert ?
        alert("Error : "+err.message+"\\\\nHMI will be reloaded.");

        // force reload ignoring cache
        location.reload(true);
    }
};

hmi_hash_u8 = new Uint8Array(hmi_hash);

var ws = null;

function send_blob(data) {
    if(ws && data.length > 0) {
        ws.send(new Blob([hmi_hash_u8].concat(data)));
    };
};

const typedarray_types = {
    SINT: (number) => new Int8Array([number]),
    INT: (number) => new Int16Array([number]),
    DINT: (number) => new Int32Array([number]),
    LINT: (number) => new Int64Array([number]),
    USINT: (number) => new Uint8Array([number]),
    UINT: (number) => new Uint16Array([number]),
    UDINT: (number) => new Uint32Array([number]),
    ULINT: (number) => new Uint64Array([number]),
    BOOL: (truth) => new Int8Array([truth]),
    NODE: (truth) => new Int8Array([truth]),
    REAL: (number) => new Float32Array([number]),
    STRING: (str) => {
        // beremiz default string max size is 128
        str = str.slice(0,128);
        binary = new Uint8Array(str.length + 1);
        binary[0] = str.length;
        for(let i = 0; i < str.length; i++){
            binary[i+1] = str.charCodeAt(i);
        }
        return binary;
    }
    /* TODO */
};

function send_reset() {
    send_blob(new Uint8Array([1])); /* reset = 1 */
};

var subscriptions = [];

function subscribers(index) {
    let entry = subscriptions[index];
    let res;
    if(entry == undefined){
        res = new Set();
        subscriptions[index] = [res,0];
    }else{
        [res, _ign] = entry;
    }
    return res
}

function get_subscription_period(index) {
    let entry = subscriptions[index];
    if(entry == undefined)
        return 0;
    let [_ign, period] = entry;
    return period;
}

function set_subscription_period(index, period) {
    let entry = subscriptions[index];
    if(entry == undefined){
        subscriptions[index] = [new Set(), period];
    } else {
        entry[1] = period;
    }
}

function reset_subscription_periods() {
    for(let index in subscriptions)
        subscriptions[index][1] = 0;
}

if(has_watchdog){
    // artificially subscribe the watchdog widget to "/heartbeat" hmi variable
    // Since dispatch directly calls change_hmi_value,
    // PLC will periodically send variable at given frequency
    subscribers(heartbeat_index).add({
        /* type: "Watchdog", */
        frequency: 1,
        indexes: [heartbeat_index],
        new_hmi_value: function(index, value, oldval) {
            apply_hmi_value(heartbeat_index, value+1);
        }
    });
}


var page_fading = "off";
var page_fading_args = "off";
function fading_page_switch(...args){
    if(page_fading == "in_progress")
        page_fading = "forced";
    else
        page_fading = "pending";
    page_fading_args = args;

    requestHMIAnimation();

}
document.body.style.backgroundColor = "black";

// subscribe to per instance current page hmi variable
// PLC must prefix page name with "!" for page switch to happen
subscribers(current_page_var_index).add({
    frequency: 1,
    indexes: [current_page_var_index],
    new_hmi_value: function(index, value, oldval) {
        if(value.startsWith("!"))
            fading_page_switch(value.slice(1));
    }
});

function svg_text_to_multiline(elt) {
    return(Array.prototype.map.call(elt.children, x=>x.textContent).join("\\\\n")); 
}

function multiline_to_svg_text(elt, str, blank) {
    str.split('\\\\n').map((line,i) => {elt.children[i].textContent = blank?"":line;});
}

function switch_langnum(langnum) {
    langnum = Math.max(0, Math.min(langs.length - 1, langnum));

    for (let translation of translations) {
        let [objs, msgs] = translation;
        let msg = msgs[langnum];
        for (let obj of objs) {
            multiline_to_svg_text(obj, msg);
            obj.setAttribute("lang",langnum);
        }
    }
    return langnum;
}

// backup original texts
for (let translation of translations) {
    let [objs, msgs] = translation;
    msgs.unshift(svg_text_to_multiline(objs[0])); 
}

var lang_local_index = hmi_local_index("lang");
var langcode_local_index = hmi_local_index("lang_code");
var langname_local_index = hmi_local_index("lang_name");
subscribers(lang_local_index).add({
    indexes: [lang_local_index],
    new_hmi_value: function(index, value, oldval) {
        let current_lang =  switch_langnum(value);
        let [langname,langcode] = langs[current_lang];
        apply_hmi_value(langcode_local_index, langcode);
        apply_hmi_value(langname_local_index, langname);
        switch_page();
    }
});

// returns en_US, fr_FR or en_UK depending on selected language
function get_current_lang_code(){
    return cache[langcode_local_index];
}

function setup_lang(){
    let current_lang = cache[lang_local_index];
    let new_lang = switch_langnum(current_lang);
    if(current_lang != new_lang){
        apply_hmi_value(lang_local_index, new_lang);
    }
}

setup_lang();

function update_subscriptions() {
    let delta = [];
    if(!ws)
        // dont' change subscriptions if not connected
        return;

    for(let index in subscriptions){
        let widgets = subscribers(index);

        // periods are in ms
        let previous_period = get_subscription_period(index);

        // subscribing with a zero period is unsubscribing
        let new_period = 0;
        if(widgets.size > 0) {
            let maxfreq = 0;
            for(let widget of widgets){
                let wf = widget.frequency;
                if(wf != undefined && maxfreq < wf)
                    maxfreq = wf;
            }

            if(maxfreq != 0)
                new_period = 1000/maxfreq;
        }

        if(previous_period != new_period) {
            set_subscription_period(index, new_period);
            if(index <= last_remote_index){
                delta.push(
                    new Uint8Array([2]), /* subscribe = 2 */
                    new Uint32Array([index]),
                    new Uint16Array([new_period]));
            }
        }
    }
    send_blob(delta);
};

function send_hmi_value(index, value) {
    if(index > last_remote_index){
        dispatch_value(index, value);

        if(persistent_indexes.has(index)){
            let varname = persistent_indexes.get(index);
            document.cookie = varname+"="+value+"; max-age=3153600000";
        }

        return;
    }

    let iectype = hmitree_types[index];
    let tobinary = typedarray_types[iectype];
    send_blob([
        new Uint8Array([0]),  /* setval = 0 */
        new Uint32Array([index]),
        tobinary(value)]);

    // DON'T DO THAT unless read_iterator in svghmi.c modifies wbuf as well, not only rbuf
    // cache[index] = value;
};

function apply_hmi_value(index, new_val) {
    // Similarly to previous comment, taking decision to update based 
    // on cache content is bad and can lead to inconsistency
    /*let old_val = cache[index];*/
    if(new_val != undefined /*&& old_val != new_val*/)
        send_hmi_value(index, new_val);
    return new_val;
}

const quotes = {"'":null, '"':null};

function eval_operation_string(old_val, opstr) {
    let op = opstr[0];
    let given_val;
    if(opstr.length < 2) 
        return undefined;
    if(opstr[1] in quotes){
        if(opstr.length < 3) 
            return undefined;
        if(opstr[opstr.length-1] == opstr[1]){
            given_val = opstr.slice(2,opstr.length-1);
        }
    } else {
        given_val = Number(opstr.slice(1));
    }
    let new_val;
    switch(op){
      case "=":
        new_val = given_val;
        break;
      case "+":
        new_val = old_val + given_val;
        break;
      case "-":
        new_val = old_val - given_val;
        break;
      case "*":
        new_val = old_val * given_val;
        break;
      case "/":
        new_val = old_val / given_val;
        break;
    }
    return new_val;
}

var current_visible_page;
var current_subscribed_page;
var current_page_index;
var page_node_local_index = hmi_local_index("page_node");
var page_switch_in_progress = false;

function toggleFullscreen() {
  let elem = document.documentElement;

  if (!document.fullscreenElement) {
    elem.requestFullscreen().catch(err => {
      console.log("Error attempting to enable full-screen mode: "+err.message+" ("+err.name+")");
    });
  } else {
    document.exitFullscreen();
  }
}

// prevents context menu from appearing on right click and long touch
document.body.addEventListener('contextmenu', e => {
    toggleFullscreen();
    e.preventDefault();
});

if(screensaver_delay){
    var screensaver_timer = null;
    function reset_screensaver_timer() {
        if(screensaver_timer){
            window.clearTimeout(screensaver_timer);
        }
        screensaver_timer = window.setTimeout(() => {
            switch_page("ScreenSaver");
            screensaver_timer = null;
        }, screensaver_delay*1000);
    }
    document.body.addEventListener('pointerdown', reset_screensaver_timer);
    // initialize screensaver
    reset_screensaver_timer();
}


function detach_detachables() {

    for(let eltid in detachable_elements){
        let [element,parent] = detachable_elements[eltid];
        parent.removeChild(element);
    }
};

function switch_page(page_name, page_index) {
    if(page_switch_in_progress){
        /* page switch already going */
        /* TODO LOG ERROR */
        return false;
    }
    page_switch_in_progress = true;

    if(page_name == undefined)
        page_name = current_subscribed_page;
    else if(page_index == undefined){
        [page_name, page_index] = page_name.split('@')
    }

    let old_desc = page_desc[current_subscribed_page];
    let new_desc = page_desc[page_name];

    if(new_desc == undefined){
        /* TODO LOG ERROR */
        return false;
    }

    if(page_index == undefined)
        page_index = new_desc.page_index;
    else if(typeof(page_index) == "string") {
        let hmitree_node = hmitree_nodes[page_index];
        if(hmitree_node !== undefined){
            let [int_index, hmiclass] = hmitree_node;
            if(hmiclass == new_desc.page_class)
                page_index = int_index;
            else
                page_index = new_desc.page_index;
        } else {
            page_index = new_desc.page_index;
        }
    }

    if(old_desc){
        old_desc.widgets.map(([widget,relativeness])=>widget.unsub());
    }
    const new_offset = page_index == undefined ? 0 : page_index - new_desc.page_index;

    const container_id = page_name + (page_index != undefined ? page_index : "");

    new_desc.widgets.map(([widget,relativeness])=>widget.sub(new_offset,relativeness,container_id));

    update_subscriptions();

    current_subscribed_page = page_name;
    current_page_index = page_index;
    let page_node;
    if(page_index != undefined){
        page_node = hmitree_paths[page_index];
    }else{
        page_node = "";
    }
    apply_hmi_value(page_node_local_index, page_node);

    jumps_need_update = true;

    requestHMIAnimation();
    let [last_page_name, last_page_index] = jump_history[jump_history.length-1];
    if(last_page_name != page_name || last_page_index != page_index){
        jump_history.push([page_name, page_index]);
        if(jump_history.length > 42)
            jump_history.shift();
    }

    apply_hmi_value(current_page_var_index, page_index == undefined
        ? page_name
        : page_name + "@" + hmitree_paths[page_index]);

    // when entering a page, assignments are evaluated
    new_desc.widgets[0][0].assign();

    return true;
};

function switch_visible_page(page_name) {

    let old_desc = page_desc[current_visible_page];
    let new_desc = page_desc[page_name];

    if(old_desc){
        for(let eltid in old_desc.required_detachables){
            if(!(eltid in new_desc.required_detachables)){
                let [element, parent] = old_desc.required_detachables[eltid];
                parent.removeChild(element);
            }
        }
        for(let eltid in new_desc.required_detachables){
            if(!(eltid in old_desc.required_detachables)){
                let [element, parent] = new_desc.required_detachables[eltid];
                parent.appendChild(element);
            }
        }
    }else{
        for(let eltid in new_desc.required_detachables){
            let [element, parent] = new_desc.required_detachables[eltid];
            parent.appendChild(element);
        }
    }

    svg_root.setAttribute('viewBox',new_desc.bbox.join(" "));
    current_visible_page = page_name;
};

/* From https://jsfiddle.net/ibowankenobi/1mmh7rs6/6/ */
function getAbsoluteCTM(element){
	var height = svg_root.height.baseVal.value,
		width = svg_root.width.baseVal.value,
		viewBoxRect = svg_root.viewBox.baseVal,
		vHeight = viewBoxRect.height,
		vWidth = viewBoxRect.width;
	if(!vWidth || !vHeight){
		return element.getCTM();
	}
	var sH = height/vHeight,
		sW = width/vWidth,
		matrix = svg_root.createSVGMatrix();
	matrix.a = sW;
	matrix.d = sH
	var realCTM = element.getCTM().multiply(matrix.inverse());
	realCTM.e = realCTM.e/sW + viewBoxRect.x;
	realCTM.f = realCTM.f/sH + viewBoxRect.y;
	return realCTM;
}

function apply_reference_frames(){
    const matches = svg_root.querySelectorAll("g[svghmi_x_offset]");
    matches.forEach((group) => {
        let [x,y] = ["x", "y"].map((axis) => Number(group.getAttribute("svghmi_"+axis+"_offset")));
        let ctm = getAbsoluteCTM(group);
        // zero translation part of CTM
        // to only apply rotation/skewing to offset vector
        ctm.e = 0;
        ctm.f = 0;
        let invctm = ctm.inverse();
        let vect = new DOMPoint(x, y);
        let newvect = vect.matrixTransform(invctm);
        let transform = svg_root.createSVGTransform();
        transform.setTranslate(newvect.x, newvect.y);
        group.transform.baseVal.appendItem(transform);
        ["x", "y"].forEach((axis) => group.removeAttribute("svghmi_"+axis+"_offset"));
    });
}

// prepare SVG
apply_reference_frames();
init_widgets();
detach_detachables();

// show main page
switch_page(default_page);

var reconnect_delay = 0;
var periodic_reconnect_timer;
var force_reconnect = false;

// Once connection established
function ws_onopen(evt) {
    // Work around memory leak with websocket on QtWebEngine
    // reconnect every hour to force deallocate websocket garbage
    if(window.navigator.userAgent.includes("QtWebEngine")){
        if(periodic_reconnect_timer){
            window.clearTimeout(periodic_reconnect_timer);
        }
        periodic_reconnect_timer = window.setTimeout(() => {
            force_reconnect = true;
            ws.close();
            periodic_reconnect_timer = null;
        }, 3600000);
    }

    // forget earlier subscriptions locally
    reset_subscription_periods();

    // update PLC about subscriptions and current page
    switch_page();

    // at first try reconnect immediately
    reconnect_delay = 1;
};

function ws_onclose(evt) {
    console.log("Connection closed. code:"+evt.code+" reason:"+evt.reason+" wasClean:"+evt.wasClean+" Reload in "+reconnect_delay+"ms.");
    ws = null;
    // Do not attempt to reconnect immediately in case:
    //    - connection was closed by server (PLC stop)
    //    - connection was closed locally with an intention to reconnect
    if(evt.code=1000 && !force_reconnect){
        window.alert("Connection closed by server");
        location.reload();
    }
    window.setTimeout(create_ws, reconnect_delay);
    reconnect_delay += 500;
    force_reconnect = false;
};

var ws_url =
    window.location.href.replace(/^http(s?:\/\/[^\/]*)\/.*$/, 'ws$1/ws')
    + '?mode=' + (has_watchdog ? "watchdog" : "multiclient");

function create_ws(){
    ws = new WebSocket(ws_url);
    ws.binaryType = 'arraybuffer';
    ws.onmessage = ws_onmessage;
    ws.onclose = ws_onclose;
    ws.onopen = ws_onopen;
}

create_ws()

var edit_callback;
const localtypes = {"PAGE_LOCAL":null, "HMI_LOCAL":null}
function edit_value(path, valuetype, callback, initial) {
    if(valuetype in localtypes){
        valuetype = (typeof initial) == "number" ? "HMI_REAL" : "HMI_STRING";
    }
    let [keypadid, xcoord, ycoord] = keypads[valuetype];
    edit_callback = callback;
    let widget = hmi_widgets[keypadid];
    widget.start_edit(path, valuetype, callback, initial);
};

var current_modal; /* TODO stack ?*/

function show_modal() {
    let [element, parent] = detachable_elements[this.element.id];

    tmpgrp = document.createElementNS(xmlns,"g");
    tmpgrpattr = document.createAttribute("transform");
    let [xcoord,ycoord] = this.coordinates;
    let [xdest,ydest] = page_desc[current_visible_page].bbox;
    tmpgrpattr.value = "translate("+String(xdest-xcoord)+","+String(ydest-ycoord)+")";

    tmpgrp.setAttributeNode(tmpgrpattr);

    tmpgrp.appendChild(element);
    parent.appendChild(tmpgrp);

    current_modal = [this.element.id, tmpgrp];
};

function end_modal() {
    let [eltid, tmpgrp] = current_modal;
    let [element, parent] = detachable_elements[this.element.id];

    parent.removeChild(tmpgrp);

    current_modal = undefined;
};

