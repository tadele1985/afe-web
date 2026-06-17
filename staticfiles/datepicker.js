console.log("Loaded");

var calendar = $.calendars.instance("ethiopian", "am");
$(".popupDatepicker").calendarsPicker({ calendar: calendar });
