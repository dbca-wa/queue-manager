var sitequeuemanager  = { 
     var: {
        'queueurl': 'false',
	'queue_group' : '',
        'running': 'false',
        'url': '',
        'session_key': '',
	'domain': ''
     },
     check_queue: function() {
        sitequeuemanager.var.running = 'true';
        console.log("check queue");
        console.log(sitequeuemanager.var.url);

        $.ajax({
          url: sitequeuemanager.var.url+'/api/check-create-session/?session_key='+sitequeuemanager.var.session_key+'&queue_group='+sitequeuemanager.var.queue_group,
          type: 'GET',
          data: {},
          cache: false,
          success: function(response) {
            if (response['session_key'] != sitequeuemanager.var.session_key) {
         	    sitequeuemanager.createCookie('sitequeuesession',response['session_key'],30);
		    sitequeuemanager.var.session_key = response['session_key'];
            }
            if (response.status == "Active") {

                          $('body').show();
                          if($("#queue-manager").length == 0) {
                          } else {
                                $("#queue-manager").remove();
                          }
		    
                  if (response['session_key'] != sitequeuemanager.var.session_key) {
			  //$('#site_queue_frame').html('<iframe src="'+sitequeuemanager.var.url+"/site-queue/set-session/?session_key="+response['session_key']+'" title="Set Session"></iframe>');
                  }

                  // sitequeuemanager.var.session_key = response['session_key'];
                  
                  if (sitequeuemanager.var.queueurl == 'true') {
		      console.log("Active Session");
		      //$('html').prepend("<div id='queue-manager'> <b>HELLO<b></div>");
                      //window.location=response.url+"/?session_key="+response['session_key'];
                  }
	    } else {
                  if($("#queue-manager" ).length == 0) {
                         $('body').hide();
                         $.ajax({
                                 url: sitequeuemanager.var.url+'/site-queue/view/',
                                 type: 'GET',
                                 data: {},
                                 cache: false,
                                 success: function(htmlresponse) {
                                            var pageheight = $( document ).height();
                                            console.log(pageheight);
                                            $('html').prepend("<div id='queue-manager' style='position: absolute; z-index: 10; height: "+pageheight+"px'><div style='height: "+pageheight+"px;  background-image: url("+'"'+"https://queue-test.digitalreach.com.au/static/img/django_queue_manager/bg_tran_black.png"+'"'+"'  >"+htmlresponse+"</div></div>");
					    if (response['queue_position'] > 0 ) {
					         $('#queue_position_div').show();
					         $('#queue_position').html(response['queue_position']);
					    }

                                 }
                          });
                  } else {
                   console.log('already exists');
                  }
                  console.log('STATUS');
                  console.log(sitequeuemanager.var.queueurl);
                  //if (sitequeuemanager.var.queueurl == 'true') {
                      // sitequeuemanager.var.session_key = response['session_key'];
		  //console.log(response['queue_position']); 
                  if (response['queue_position'] > 0 ) {
                      $('#queue_position_div').show();
                      $('#queue_position').html(response['queue_position']);
                  }
		  if (sitequeuemanager.var.queueurl == 'true') {
                  } else {
	              console.log("InActive Session");
		      // $('html').prepend("<div id='queue-manager'> <b>HELLO<b></div>");
                      // window.location=sitequeuemanager.var.url+response.queueurl+"?session_key="+response['session_key'];
                  }

	    }
            setTimeout(function() { sitequeuemanager.check_queue(); },5000);
          },
          error: function(response) {
             console.log('error connecting to queue system,  will try again soon');
             setTimeout(function() { sitequeuemanager.check_queue(); },20000);
          }
        });

     },
     getQueryParam: function(param, defaultValue = undefined) {
         location.search.substr(1)
             .split("&")
             .some(function(item) { // returns first occurence and stops
                 return item.split("=")[0] == param && (defaultValue = item.split("=")[1], true)
             })
         return defaultValue
     },
     ReadCookie: function(name) {
         var nameEQ = name + "=";
         var ca = document.cookie.split(';');
	 ca = ca.reverse();
         for (var i = 0; i < ca.length; i++) {
             var c = ca[i];
             while (c.charAt(0) == ' ') c = c.substring(1, c.length);
             if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length, c.length);
         }
         return null;
     },	
     createCookie: function(name, value, days) {
         var expires;
     
         if (days) {
             var date = new Date();
             date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
             expires = "; expires=" + date.toGMTString();
         } else {
             expires = "";
         }
         document.cookie = encodeURIComponent(name) + "=" + encodeURIComponent(value) + expires + "; path=/; domain=."+sitequeuemanager.var.domain;
     },
     init: function(queue_domain,queue_url, queue_group) {
	 console.log(queue_url);
         sitequeuemanager.var.domain = queue_domain;
	 sitequeuemanager.var.url = queue_url;
         sitequeuemanager.var.queue_group = queue_group;

         if (window.jQuery) {
              var smactive = true;

              if ($('#site_queue_manager_active').length > 0) {
                    var site_queue_manager_active = $('#site_queue_manager_active').val();
                    if (site_queue_manager_active == 'disabled') {
	               smactive = false;
                    }
              }

              if (smactive == true) { 
                  if ($('#site_queue_frame').length == 0) { 
                     // $('html').append('<div id="site_queue_frame" style="idisplay:none;"> IFRAME</div>');
	             // $('#site_queue_frame').html('<iframe src="'+sitequeuemanager.var.url+"/site-queue/set-session/"+' title="Set Session"></iframe>');
                  }
                  session_key = sitequeuemanager.getQueryParam('session_key');
                  if (session_key != undefined || session_key !=null) {
		      if (session_key.length > 10) { 
                         // sitequeuemanager.createCookie('session_key',session_key,1)
                         sitequeuemanager.createCookie('sitequeuesession',session_key,30);
                         sitequeuemanager.var.session_key = session_key;
		      }
                      // $('#site_queue_frame').html('<iframe src="'+sitequeuemanager.var.url+"/site-queue/set-session/?session_key="+session_key+'" title="Set Session"></iframe>');
	          } else {
		       console.log('CCOOKE');
                       console.log(sitequeuemanager.ReadCookie('sitequeuesession'));
                       console.log(sitequeuemanager.ReadCookie('_ga'));
                       console.log(document.cookie);
		       if (sitequeuemanager.ReadCookie('sitequeuesession')) { 
		          sitequeuemanager.var.session_key = sitequeuemanager.ReadCookie('sitequeuesession');
                       } 
	          }
                  //if ("parkstayUrl" in window) {
	          //      sitequeuemanager.var.url = parkstayUrl;
	          // }

                  // if (window.jQuery) {
                  //     // jQuery is loaded
                  // } else {

                  //       var scriptTag = document.createElement('script');
                  //       scriptTag.src = sitequeuemanager.var.url+'/static/js/django_queue_manager/jquery-3.5.1.js';
                  //       //scriptTag.onload = "sitequeuemanager.check_queue();";
                  //       document.head.appendChild(scriptTag);
                  //       setTimeout(function() { sitequeuemanager.init();}, 200);
                  //     // jQuery is not loaded
                  //  //   alert("Doesn't Work");
                  // }

                  if (window.jQuery) {
                      sitequeuemanager.var.queueurl = 'false';
                      // if ($("#queue").length> 0) {
                      //      var queue = $("#queue").val();
                      //      if (queue == 'true') {
                      //         sitequeuemanager.var.queueurl = 'true';
                      //      }
                      //}
                      if (sitequeuemanager.var.running == 'false' ) {
                          sitequeuemanager.check_queue();
                      }
                  }
              }
          } else {
                 var scriptTag = document.createElement('script');
                 scriptTag.src = sitequeuemanager.var.url+'/static/js/django_queue_manager/jquery-3.5.1.js';
                 //scriptTag.onload = "sitequeuemanager.check_queue();";
                 document.head.appendChild(scriptTag);
                 setTimeout(function() { sitequeuemanager.init(queue_domain,queue_url);}, 200);
	  }

     }

}
//sitequeuemanager.init();
//$ (document).resize (function () {
//console.log($( document ).height());
//})
