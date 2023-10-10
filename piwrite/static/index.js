window.onerror = function(e, source, lineno, colno, error){
  document.getElementById('err').innerText = e.toString() + " " + lineno + " " + error;
}

function piwrite(){
  const socket = io()

  socket.on('connect', function () {
    console.log('created connection')
  });

  socket.on('error', function (e) {
    if(!e.data || e.data == ""){
      return
    }
    document.getElementById("status").innerHTML = e.data
  });

  socket.on('completions', function (e) {
    document.getElementById("completions").innerHTML = e.data
  });
  socket.on('fontsize', function (e) {
    if(!e.data || e.data == ""){
      return
    }
    document.getElementById("field").style.fontSize = e.data + "pt"
    document.getElementById("visual").style.fontSize = e.data + "pt"
  })

  socket.on('dot', function (e) {
    console.log("Receiving dot:")
    console.log(e)
    if(!e.data || e.data == ""){
      return
    }
    if(e.data == "nope"){
      document.getElementById("wrapper").style.display = "block"
      document.getElementById("graph").style.display = "none"
      document.getElementById("graph").src = ""
    } else {
      document.getElementById("wrapper").style.display = "none"
      document.getElementById("graph").src = e.data
      document.getElementById("graph").style.display = "block"
    }
  })

  function addStyle(elem, stylename){
    styles = ["monospace", "serif", "sans", "latex"]
    for(i=0;i<styles.length;i++){
      // Missing let of here, blame the old browser in the Kindle
      style = styles[i]
      if(style==stylename){
        elem.classList.add(stylename)
      }else{
        elem.classList.remove(style)
      }
    }
  }

  socket.on('font', function (e) {
    if(!e.data || e.data == ""){
      return
    }
    field = document.getElementById("field")
    visual = document.getElementById("visual")
    if(e.data == "mono"){
      addStyle(field, "monospace")
      addStyle(visual, "monospace")
    }
    if(e.data == "serif"){
      addStyle(field, "serif")
      addStyle(visual, "serif")
    }
    if(e.data == "sans"){
      addStyle(field, "sans")
      addStyle(visual, "sans")
    }
    if(e.data == "latex"){
      addStyle(field, "latex")
      addStyle(visual, "latex")
    }
  });

  rotated = false

  socket.on('status', function (e) {
    if(!e.data || e.data == ""){
      return
    }
    document.getElementById("status").innerHTML = e.data
  });

  socket.on('rot', function (e) {
    if(!e.data || e.data == ""){
      return
    }
    if(e.data == "0"){
      document.body.classList.remove("rot90")
      document.getElementById("bottom").classList.remove("rotbottom")
      rotated = false
    }else{
      document.body.classList.add("rot90")
      document.getElementById("bottom").classList.add("rotbottom")
      rotated = true
    }
  });

  socket.on('visual', function (e) {  
    console.log("Receiving visual")
    // Having to use height is one of those barfs of the Kindle browser
    if(!e.data || e.data.length == 0){
      document.getElementById("wrapper").style.height = "auto"
      document.getElementById("wrapper").style.overflow = "hidden" 
      document.getElementById("visual").innerHTML = ""
      document.getElementById("visual").style.display = "none"
    } else {
      document.getElementById("visual").innerHTML = e.data.join("")
      document.getElementById("visual").style.display = "block"
      document.getElementById("wrapper").style.height = 0
      document.getElementById("wrapper").style.overflow = "hidden"
    }
  }); 

  socket.on('modal', function (e) {
    console.log("Receiving modal:")
    console.log(e)
    if(e.data == ""){
      document.getElementById("modal").style.display = "none"
      document.getElementById("modal").innerHTML = ""
      document.getElementById("field").style.opacity = 1
    } else {
      document.getElementById("modal").style.display = "block"
      document.getElementById("modal").innerHTML = e.data
      document.getElementById("field").style.opacity = 0.3
    }
  });

  socket.on('command', function (e) {
    document.getElementById("status").innerHTML = e.data
  });

  socket.on('mode', function (e) {
    document.getElementById("mode").innerHTML = e.data
  });

  socket.on('saved', function (e) {
    if(e.data){
      document.getElementById("saved").innerHTML = "&nbsp;"
    } else {
      document.getElementById("saved").innerHTML = "*"
    }
  });

  socket.on('filename', function(e) {
    document.getElementById("filename").innerHTML = e.data
  })

  socket.on('buffer', function (e) {
    document.getElementById("field").innerHTML = e.data.join("")
    range = document.createRange()
    range.setStartBefore(document.getElementById("caret"))
    range.setEndAfter(document.getElementById("caret"))
    clientRect = range.getBoundingClientRect()
    if(rotated){
      return
    } else {
      curr = document.getElementById("field").getBoundingClientRect().top 
      adjusted = curr-clientRect.top
      if(Math.abs(clientRect.top)>200){
        adjusted+=200
      }
    }
    document.getElementById("field").style.top = adjusted+"px"
  });
}
