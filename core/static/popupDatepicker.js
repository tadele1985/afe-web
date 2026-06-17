$("#l10nCal").change(function () {
	$("#l10nLanguage")
		.html(formatLanguages($(this).val()))
		.change();
});

$("#l10nLanguage").change(function () {
	const name = $("#l10nCal").val();
	const loadName = name == "julian" ? "" : name;
	const lang = $(this).val();
	if (lang) {
		$.localise("js/jquery.calendars" + (loadName ? "." : "") + loadName, lang);
	}
	const calendar = $.calendars.instance(name, lang);
	$("#l10n ul").toggleClass("l10nRTL", calendar.local.isRTL);
	let list = "";
	for (let i = 0; i < calendar.local.dayNames.length; i++) {
		list += "<li>" + calendar.local.dayNames[i] + "</li>";
	}
	$("#l10nDays").empty().html(list);
	list = "";
	for (let i = 0; i < calendar.local.monthNames.length; i++) {
		list += "<li>" + calendar.local.monthNames[i] + "</li>";
	}
	$("#l10nMonths").empty().html(list);
	$("#l10nFormat").val(calendar.local.dateFormat);
	$("#l10nFirstDay").val(calendar.local.dayNames[calendar.local.firstDay]);
});

var calendar = $.calendars.instance("ethiopian", "am");
$(".popupDatepicker").calendarsPicker({ calendar: calendar });

document.addEventListener("htmx:afterSwap", (ev) => {
	if (
		ev.target.classList.contains("popupDatepicker") ||
		ev.target.querySelectorAll(".popupDatepicker").length > 0
	) {
		var calendar = $.calendars.instance("ethiopian", "am");
		$(".popupDatepicker").calendarsPicker({ calendar: calendar });
	}
});

document.addEventListener("DOMContentLoaded", () => {
	htmx.onLoad((content) => {
		console.log("OUT: ", ev.target);
		if (
			content.classList.contains("popupDatepicker") ||
			content.querySelectorAll(".popupDatepicker").length > 0
		) {
			console.log("HERE: ", ev.target);
			var calendar = $.calendars.instance("ethiopian", "am");
			$(".popupDatepicker").calendarsPicker({ calendar: calendar });
		}
	});
});
function initializeDatepicker() {
	$(".popupDatepicker").calendarsPicker({ calendar: calendar });
	console.log("Loaded out: ", document.querySelector(".popupDatepicker"));
}

initializeDatepicker();

document.addEventListener("DOMContentLoaded", () => {
	$(".popupDatepicker").calendarsPicker({ calendar: calendar });

	const targetNode = document.querySelector("body");

	// Configuration options for the observer
	const config = { childList: true, subtree: true };

	// Callback function executed when mutations are observed
	const callback = (mutationsList) => {
		for (const mutation of mutationsList) {
			if (mutation.type !== "childList") return;
			// Check added nodes for a specific class
			for (const node of mutation.addedNodes) {
				if (node.nodeType !== 1) continue;
				console.log("Mutated for: ", node);
				if (
					node.classList.contains("popupDatepicker") ||
					node.querySelectorAll(".popupDatepicker").length > 0
				) {
					console.log("Run for: ", node);
					$(".popupDatepicker").calendarsPicker({ calendar: calendar });
					// $(node).calendarsPicker({ calendar: calendar });
				}
			}
			// mutation.addedNodes.forEach((node) => {
			//   if (node.nodeType !== 1) continue;
			//   if (node.nodeType === 1 && node.classList.contains("popupDatepicker")) {
			//     console.log("New element mounted: ", node);
			//     // Perform actions for the new element
			//     $(node).calendarsPicker({ calendar: calendar });
			//     console.log("New popupDatepicker added:", node);
			//   }
			// });
		}
	};

	// Create an observer instance
	const observer = new MutationObserver(callback);

	// Start observing the target node with the specified configuration
	observer.observe(targetNode, config);
});

// $(function () {
//   //	$.calendars.picker.setDefaults({renderer: $.calendars.picker.themeRollerRenderer}); // Requires jquery.calendars.picker.ext.js
//   var calendar = $.calendars.instance("ethiopian", "am");
//   $(".popupDatepicker").calendarsPicker({ calendar: calendar });
//   console.log("Loaded me: ", document.querySelector(".popupDatepicker"));
// });
