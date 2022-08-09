
	function SubmitUser(){
		var username = document.getElementById("username").value
		document.getElementById("submitbutton").innerHTML = "<i>Running</i>"
		document.getElementById("results").innerHTML = ""

		
		$.get(baseURL + "/subredditlist", {}, function(subreddits){
			//go through each subreddit
			subreddits.forEach(sr => {
				console.log(sr + "...")
				$.ajax({async: false, type: 'GET', url:baseURL + "/subreddituserdata", data:{"username": username, "subreddit": sr}, success: function(resp){
					console.log(resp);
					document.getElementById("results").innerHTML += resp.result_str + "<br>";
					}
				});

			}); //end of foreach

			console.log("DONE!")
			document.getElementById("submitbutton").innerHTML = "Check"
		});

	}

	$.get(baseURL + "/subredditlist", {}, function(resp){
		console.log(resp)
	});