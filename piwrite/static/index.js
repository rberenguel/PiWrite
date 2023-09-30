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
    document.getElementById("field").style.fontSize = e.data + "px"
    })

  socket.on('font', function (e) {
    if(!e.data || e.data == ""){
      return
    }
    if(e.data == "mono"){
      document.getElementById("field").classList.add("monospace")
      document.getElementById("field").classList.remove("serif")
      document.getElementById("field").classList.remove("sans")
      document.getElementById("field").classList.remove("latex")
    }
    if(e.data == "serif"){
      document.getElementById("field").classList.add("serif")
      document.getElementById("field").classList.remove("monospace")
      document.getElementById("field").classList.remove("sans")
      document.getElementById("field").classList.remove("latex")
    }
    if(e.data == "sans"){
      document.getElementById("field").classList.add("sans")
      document.getElementById("field").classList.remove("monospace")
      document.getElementById("field").classList.remove("serif")
      document.getElementById("field").classList.remove("latex")
    }
    if(e.data == "latex"){
      document.getElementById("field").classList.add("latex")
      document.getElementById("field").classList.remove("monospace")
      document.getElementById("field").classList.remove("serif")
      document.getElementById("field").classList.remove("sans")
    }
    });


  socket.on('status', function (e) {
    if(!e.data || e.data == ""){
      return
    }
    document.getElementById("status").innerHTML = e.data
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
      curr = document.getElementById("field").getBoundingClientRect().top 
      adjusted = curr-clientRect.top
      if(Math.abs(clientRect.top)>500){
        adjusted+=200
      }
      document.getElementById("field").style.top = adjusted+"px"
   });
}
