// import Nevow.Athena
// import Divmod.Base

function updateAttr(id, param, value) {
  Nevow.Athena.Widget.fromAthenaID(1).callRemote('HMIexec', 'setattr', id, param, value);
}

var svguiWidgets = new Array();

var currentObject = null;
function setCurrentObject(obj) {
	currentObject = obj;
}
function isCurrentObject(obj) {
	return currentObject == obj;
}

function getSVGElementById(id) {
	return document.getElementById(id);
}

function blockSVGElementDrag(element) {
	element.addEventListener("draggesture", function(event){event.stopPropagation()}, true);
}

LiveSVGPage.LiveSVGWidget = Nevow.Athena.Widget.subclass('LiveSVGPage.LiveSVGWidget');
LiveSVGPage.LiveSVGWidget.methods(

    function handleEvent(self, evt) {
        if (currentObject != null) {
            currentObject.handleEvent(evt);
        }
    },

    function receiveData(self, data){
        dataReceived = json_parse(data);
        gadget = svguiWidgets[dataReceived.id]
        if (gadget) {
        	gadget.updateValues(json_parse(dataReceived.kwargs));
        }
        //console.log("OBJET : " + dataReceived.back_id + " STATE : " + newState);
    },
    
    function init(self, arg1){
        //console.log("Object received : " + arg1);
        for (ind in arg1) {
            gad = json_parse(arg1[ind]);
            args = json_parse(gad.kwargs);
            gadget = new svguilib[gad.__class__](self, gad.id, args);
            svguiWidgets[gadget.id]=gadget;
            //console.log('GADGET :' + gadget);
        }
        var elements = document.getElementsByTagName("svg");
        for (var i = 0; i < elements.length; i++) {
        	elements[i].addEventListener("mouseup", self, false);
        }
        //console.log("SVGUIWIDGETS : " + svguiWidgets);
    }
);
