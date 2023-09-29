window.onerror = function(e, source, lineno, colno, error){
  document.getElementById('err').innerText = e.toString() + " " + lineno + " " + error;
}

function piwrite(){
  const socket = io()

  socket.on('connect', function () {
    console.log('created connection')
  });

  socket.on('error', function (e) {
    console.log('error', e)
    if(!e.data || e.data == ""){
      return
    }
     document.getElementById("status").innerHTML = e.data
  });
  
  socket.on('completions', function (e) {
    console.log('completions', e)
    document.getElementById("completions").innerHTML = e.data
  });
  socket.on('fontsize', function (e) {
    console.log('fontsize', e)
    if(!e.data || e.data == ""){
      return
    }
    console.log("Setting font size to "+e.data) // Kindle's browser does not accept ` strings
    document.getElementById("fieldcontainer").style.fontSize = e.data + "px"
    })

  socket.on('font', function (e) {
    console.log('font', e)
    if(!e.data || e.data == ""){
      return
    }
    if(e.data == "mono"){
      console.log("Setting font to mono")
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
    console.log('status', e)
    if(!e.data || e.data == ""){
      return
    }
    document.getElementById("status").innerHTML = e.data
  });


  socket.on('command', function (e) {
    console.log('command', e)
    document.getElementById("status").innerHTML = e.data
  });


  socket.on('mode', function (e) {
    console.log('mode switch', e)
    document.getElementById("mode").innerHTML = e.data
  });
 
  socket.on('saved', function (e) {
    console.log('save switch', e)
    if(e.data){
      document.getElementById("saved").innerHTML = ""
    } else {
      document.getElementById("saved").innerHTML = "*"
    }
  });

  socket.on('filename', function(e) {
    console.log(e)
    document.getElementById("filename").innerHTML = e.data
  })

  socket.on('buffer', function (e) {
    console.log(e)
    document.getElementById("field").innerHTML = e.data.join("")
  });
}
