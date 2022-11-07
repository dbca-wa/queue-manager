var sitequeuemanager = { 
     var: {
        'queueurl': 'false',
	'queue_group' : '',
        'running': 'false',
        'url': '',
        'session_key': '',
	'domain': '',
        'browser_inactivity_time': 0,
	'time_left_enabled': false,
	'show_queue_position': false,
	'browser_inactivity_timeout': 60, 
	'browser_inactivity_redirect': '',
	'browser_inactivity_enabled': false,
	'waiting_queue_enabled': true,
	'custom_message': '',
	'queue_name' : '',
        'more_info_link' : '',
	'max_queue_session_limit': '100000',
	'max_queue_url_redirect': '/'
     },
     check_queue: function() {
        sitequeuemanager.var.running = 'true';
        console.log("check queue");

        $.ajax({
          url: sitequeuemanager.var.url+'/api/check-create-session/?session_key='+sitequeuemanager.var.session_key+'&queue_group='+sitequeuemanager.var.queue_group,
          type: 'GET',
          data: {},
          cache: false,
          success: function(response) {
            sitequeuemanager.var.time_left_enabled = response['time_left_enabled'];
            sitequeuemanager.var.show_queue_position = response['show_queue_position'];
            sitequeuemanager.var.browser_inactivity_timeout = response['browser_inactivity_timeout'];
            sitequeuemanager.var.browser_inactivity_redirect = response['browser_inactivity_redirect'];
	    sitequeuemanager.var.waiting_queue_enabled = response['waiting_queue_enabled'];
	    sitequeuemanager.var.browser_inactivity_enabled = response['browser_inactivity_enabled'];
            sitequeuemanager.var.custom_message = response['custom_message'];
            sitequeuemanager.var.queue_name = response['queue_name'];
            sitequeuemanager.var.max_queue_session_limit = response['max_queue_session_limit']
            sitequeuemanager.var.max_queue_url_redirect = response['max_queue_url_redirect']

	    if (response['more_info_link'] == null) {
                sitequeuemanager.var.more_info_link = "";
            } else {
                sitequeuemanager.var.more_info_link = response['more_info_link'];
            }

            if (response['session_key'] != sitequeuemanager.var.session_key) {
         	    sitequeuemanager.createCookie('sitequeuesession',response['session_key'],30);
		    sitequeuemanager.var.session_key = response['session_key'];
            }

            if (response.status == "Active") {
		          // show session timer box on active session
		          if (sitequeuemanager.var.time_left_enabled == true) {
			      var timelimit = 'N/A';
                              if (response['expiry_seconds'] > 60) {
                                   var expiry_min = response['expiry_seconds'] / 60;
				   timelimit = parseInt(expiry_min)+" min";
			      } else {
				   $('#queue-time-left').fadeOut(2000);$('#queue-time-left').fadeIn(2000);
                                   timelimit = "<1min";
			      }
                          if($("#queue-timer" ).length == 0) {
                              $('html').prepend("<div id='queue-timer' style='position: absolute; z-index: 10; width:100%; '><div align='right'><div style='border: 1px solid #484747; padding: 12px 10px 10px 10px; width: 90px; height: 90px; margin-top: 3px; margin-right:  15px;  border-radius: 5px; font-size:16px; background: rgb(0 0 0 / 80%); color: #FFF;' >Time Left<br><div id='queue-time-left' style='font-size: 19px; padding-top: 10px; text-align: center;'>N/A</div></div></div></div>");
		          }
                          $('#queue-time-left').html(timelimit);
                          } else {
                              $("#queue-timer" ).remove();
		          }

                          // hide and remove waiting screen.
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
			  
			 $("#queue-timer" ).remove();
                         $.ajax({
                                 url: sitequeuemanager.var.url+'/site-queue/view/',
                                 type: 'GET',
                                 data: {},
                                 cache: false,
                                 success: function(htmlresponse) {
                                            var pageheight = $( document ).height();
                                            console.log(pageheight);
                                            $('html').prepend("<div id='queue-manager' style='position: absolute; z-index: 10; width: 100%; height: "+pageheight+"px'><div style='width: 100%; height: 100%;  background-image: url("+'"'+sitequeuemanager.var.url+"/static/img/django_queue_manager/bg_tran_black.png"+'"'+"'  >"+htmlresponse+"</div></div>");
					    if (response['queue_position'] > 0 ) {
					         $('#queue_position_div').show();
					         $('#queue_position').html(response['queue_position']);
						 $('#wait_time').html(response['wait_time']+' minute/s');
						 if (sitequeuemanager.var.custom_message.length > 0) {
						     $("#waitingmessage").html(sitequeuemanager.var.custom_message);
					         }
						 if (sitequeuemanager.var.queue_name.length > 0) {
                                                     $("#queue-name").html(sitequeuemanager.var.queue_name);
						 }
						
						 if (sitequeuemanager.var.more_info_link.length > 0) {
                                                     $("#more_info_link").attr("href", sitequeuemanager.var.more_info_link);
					             $("#more_info_div").show();
					         } else {
                                                     $("#more_info_div").hide();
					         }


					    }
                                 }
                          });
                  } else {
		       
		       $("#queue-manager" ).show();
                       console.log('already exists');
                  }
                  if (response['queue_position'] > 0) {
                      $('#queue_position_div').show();
                      if (response['queue_position']  > sitequeuemanager.var.max_queue_session_limit) { 
			      window.location = sitequeuemanager.var.max_queue_url_redirect;
		      }

		      if (sitequeuemanager.var.show_queue_position == true) { 
                         $('#div_queue_position').show();
		      } else {
                         $('#div_queue_position').hide();
	              }
                      $('#queue_position').html(response['queue_position']);
		      $('#wait_time').html(response['wait_time']+' minute/s');
		      sitequeuemanager.var.browser_inactivity_time = 0;
		      if (sitequeuemanager.var.custom_message.length > 0) {
                             $("#waitingmessage").html(sitequeuemanager.var.custom_message);
		      }
                      if (sitequeuemanager.var.queue_name.length > 0) {
                          $("#queue-name").html(sitequeuemanager.var.queue_name);
                      }
                      if (sitequeuemanager.var.more_info_link.length > 0) {
                          $("#more_info_link").attr("href", sitequeuemanager.var.more_info_link);
                          $("#more_info_div").show();
                      } else {
                          $("#more_info_div").hide();
                      }


                  }
		  if (sitequeuemanager.var.queueurl == 'true') {
                  } else {
	              console.log("InActive Session");
		      // $('html').prepend("<div id='queue-manager'> <b>HELLO<b></div>");
                      // window.location=sitequeuemanager.var.url+response.queueurl+"?session_key="+response['session_key'];
                  }

	    }
            setTimeout(function() { sitequeuemanager.check_queue(); },8000);
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
     inActivityCountDown: function() {
	    var countdown = $('#qm-countdown').html();
	    countdown = countdown - 1;
	    if (countdown < 0) {
              window.location = sitequeuemanager.var.browser_inactivity_redirect;
            }
	    $('#qm-countdown').html(countdown);

     },
     inactivityConfirm: function() {
     
      $('#qm-countdown').html('45');
      sitequeuemanager.var.browser_inactivity_time = 0;
      $("#queue-inactivity" ).remove();

     },	      
     timerIncrement: function() {
         sitequeuemanager.var.browser_inactivity_time = sitequeuemanager.var.browser_inactivity_time + 1;
	 if (sitequeuemanager.var.waiting_queue_enabled == true ) {
	       if (sitequeuemanager.var.browser_inactivity_enabled == true) { 
                    if (sitequeuemanager.var.browser_inactivity_time > sitequeuemanager.var.browser_inactivity_timeout) {
	                  var pageheight = $( document ).height();
	                  if($("#queue-inactivity" ).length == 0) {
                              $('html').prepend("<div id='queue-inactivity' style='width: 100%; position: absolute; z-index: 10; height: "+pageheight+"px'><div style='width: 100%; height: "+pageheight+"px;  background-image: url("+'"'+sitequeuemanager.var.url+"/static/img/django_queue_manager/bg_tran_black.png"+'"'+"'  ><BR><BR><div class='qm-box'><img src='"+sitequeuemanager.var.url+"/static/img/django_queue_manager/exclamation.png'><br><br> We have detected that you have been inactive on our site for a while. <br><br> Are you still browsing the site? <br><br><button class='qm-button qm-blue' onclick='sitequeuemanager.inactivityConfirm();'>Yes, I am</button>&nbsp;<button class='qm-button qm-red' id='qm-countdown'>30</button></div></div></div>");
	                         
	                      sitequeuemanager.var.idleInterval = setInterval(sitequeuemanager.inActivityCountDown, 1000);

	                  }
	                  // var idleInterval = setInterval(sitequeuemanager.timerIncrement, 15000);
                         
                    }
	       }
         }
     },
     init: function(queue_domain,queue_url, queue_group, active_hosts="") {
        sitequeuemanager.var.domain = queue_domain;
	    sitequeuemanager.var.url = queue_url;
        sitequeuemanager.var.queue_group = queue_group;
        current_host = window.location.host;

        $( window ).resize(function() { $('#queue-manager').height($( document ).height());});
         
	 var queue_js_active = false;
	 if (active_hosts == '*') {
                queue_js_active = true;
         } else {
	     ah = active_hosts.split(",")
	     for (h in ah) {
                if (current_host == ah[h]) {
                    queue_js_active = true;
                }
             }
	 }

	 if (queue_js_active == false) {
            console.log('Url does not match active urls');
            return;
         }

	 var idleInterval = setInterval(sitequeuemanager.timerIncrement, 1000);
         $(document).mousemove(function (e) {
             sitequeuemanager.var.browser_inactivity_time = 0;
         });

         $(document).keypress(function (e) {
             sitequeuemanager.var.browser_inactivity_time = 0;
         });

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

                  if (window.jQuery) {
		      
                      sitequeuemanager.var.queueurl = 'false';
                      // if ($("#queue").length> 0) {
                      //      var queue = $("#queue").val();
                      //      if (queue == 'true') {
                      //         sitequeuemanager.var.queueurl = 'true';
                      //      }
                      //}
                      if (sitequeuemanager.var.running == 'false' ) {
			  console.log('loading css');
			  var cssTag = document.createElement('link');
			  cssTag.href = sitequeuemanager.var.url+"/static/css/django_queue_manager/queue-manager.css";
                          cssTag.type='text/css';
			  cssTag.rel='stylesheet';	      
                          document.head.appendChild(cssTag);

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


