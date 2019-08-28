odoo.define('web_gantt_native.ResLevel', function (require) {
"use strict";

var Widget = require('web.Widget');
var time = require('web.time');



// function get_data_ghosts (parentg) {

        // var ghosts = parentg.gantt.data.Ghost;
        // var ghost_id = parentg.fields_view.arch.attrs.ghost_id;
        // var ghost_ids_name = parentg.fields_view.arch.attrs.ghost_name;
        // var ghost_ids_date_start = parentg.fields_view.arch.attrs.ghost_date_start;
        // var ghost_ids_date_end = parentg.fields_view.arch.attrs.ghost_date_end;
        // var ghost_ids_durations = parentg.fields_view.arch.attrs.ghost_durations;
        //
        // var data_ghosts = _.map(ghosts, function(ghost) {
        //
        //         var data_row_id = ghost[ghost_id][0];
        //
        //         var durations = ghost[ghost_ids_durations];
        //
        //         var date_start = time.auto_str_to_date(ghost[ghost_ids_date_start]);
        //         if (!date_start){
        //             return
        //         }
        //         var date_end = time.auto_str_to_date(ghost[ghost_ids_date_end]);
        //         if (!date_end){
        //
        //             if (durations){
        //                 date_end = moment(date_start).add(durations*60, 'minutes')._d;
        //             }
        //             else{
        //                 return
        //             }
        //         }
        //
        //         return {
        //             data_row_id: data_row_id,
        //             name : ghost[ghost_ids_name],
        //             date_start : date_start,
        //             date_end : date_end,
        //             durations : ghost[ghost_ids_durations]
        //     }
        // });
        //
        // try {
        //     var data_min = _.min(data_ghosts, function (ghost) {
        //         return ghost.date_start;
        //     });
        // }
        // catch (err) {}
        //
        //
        // try {
        //     var data_max = _.max(data_ghosts, function (ghost) {
        //         return ghost.date_end;
        //     });
        // }
        // catch (err) {}
        //
        //
        //
        // try {
        //     var start_time = data_min["date_start"].getTime();
        //     parentg.GtimeStopA = parentg.GtimeStopA.concat(start_time);
        // } catch (err) {}
        //
        // try {
        //     var stop_time = data_max["date_end"].getTime();
        //     parentg.GtimeStartA = parentg.GtimeStartA.concat(stop_time);
        // } catch (err) {}
        //
        //
        // return data_ghosts;



// }


    function secondsToTime(secs)
{


    // var hours = Math.floor(secs / (60 * 60));
    //
    // var divisor_for_minutes = secs % (60 * 60);
    // var minutes = Math.floor(divisor_for_minutes / 60);
    //
    // var divisor_for_seconds = divisor_for_minutes % 60;
    // var seconds = Math.ceil(divisor_for_seconds);
    //
    // var obj = {
    //     "h": hours,
    //     "m": minutes,
    //     "s": seconds
    // };
    // return obj;

    var pad = function(num, size) { return ('000' + num).slice(size * -1); },
    time = parseFloat(secs).toFixed(3),
    hours = Math.floor(time / 60 / 60),
    minutes = Math.floor(time / 60) % 60,
    seconds = Math.floor(time - minutes * 60),
    milliseconds = time.slice(-3);

        var obj = {
        "h": pad(hours, 2),
        "m": pad(minutes, 2),
        "s":  pad(seconds, 2)
    };
    return obj;

}

//
// function sec2time(timeInSeconds) {
//
//
//     return pad(hours, 2) + ':' + pad(minutes, 2) + ':' + pad(seconds, 2) + ',' + pad(milliseconds, 3);
// }


var GanttTimeLineResLevel = Widget.extend({
    template: "GanttTimeLine.reslevel",

    init: function(parent) {
        this._super.apply(this, arguments);
    },


    start: function(){

        var parentg =  this.getParent();

        var data_widgets =  parentg.gantt_timeline_data_widget;
        var data_load = parentg.Load_Data;



        if (data_load){

            // S1
             var data_load_s1 = _.map(data_load, function (res_data) {
                    return {
                        data_aggr: res_data["data_aggr"],
                        duration : res_data["duration"],
                        load_id : res_data["resource_id"] ? res_data["resource_id"][0] : -1
                }
             });

             // S2
             var data_load_s2 = _.groupBy(data_load_s1, 'load_id' );

             // S3
             var data_load_s3 = _.map(data_load_s2, function (value, key) {

                 var data_group = _.groupBy(value, 'data_aggr' );
                 return {
                        load_id : parseInt(key) || -1,
                        data_group: data_group
                 }
             });


             _.each(data_widgets, function(widget) {

                if (widget.record.is_group) {

                    var row_id = widget.record["group_id"] ? widget.record["group_id"][0] : -1;
                    var data_load_w = _.where(data_load_s3, {load_id: row_id});

                    // Get Load Data
                    if (typeof data_load_w !== 'undefined' && data_load_w.length > 0 ){

                        var data_group = data_load_w[0]["data_group"];

                        var gp_load =  _.map(data_group , function (data_load_value, key) {


                            var duration =  _.reduce(data_load_value,
                            function (memoizer, value) {
                                return memoizer + value.duration;
                            }, 0);

                            var r_obj = [];
                            r_obj["date"] = key;
                            r_obj["duration"] = duration;

                            return r_obj
                        });
                    }

                    var rowdata = widget.$el;

                    // Render Load Data
                    _.each(gp_load, function(link_load){

                        var date_point = time.auto_str_to_date(link_load.date);
                        var start_time = date_point.getTime();

                        var left_point = Math.round((start_time-parentg.firstDayScale) / parentg.pxScaleUTC);

                        var load_bar_x = $('<div class="task-gantt-bar-load"></div>');

                        // var duration_seconds = humanizeDuration(parseInt(link_load.duration, 10)*1000, {round: true });

                        var duration_ = secondsToTime(link_load.duration);



                        var bar_W = 20;
                        var one_line = false;
                        if (parentg.timeType === "day_1hour"){
                            bar_W =  2 * bar_W * 24;
                            one_line = true
                        }
                        else if (parentg.timeType === "day_2hour"){
                            bar_W =  2 *  bar_W * 12;
                            one_line = true
                        }else if (parentg.timeType === "day_4hour"){
                            bar_W =  2 *  bar_W * 6;
                            one_line = true
                        }else if (parentg.timeType === "day_8hour"){
                            bar_W =  2 *  bar_W * 3;
                            one_line = true
                        }



                        if (one_line){

                            bar_W = bar_W - 10;
                            left_point = left_point + 5;

                            var _m = '';
                            if (duration_.m !== "00") {
                                _m = ' : '+duration_.m;

                            }
                            var bar_one_line = $('<div class="task-gantt-load-duration_l">'+duration_.h+''+_m+'</div>');

                            bar_one_line.css({"font-size": '1.0em'});
                            load_bar_x.css({"background": 'rgba(223, 224, 222, 0.3)'});


                            load_bar_x.append(bar_one_line)



                        }else{
                            load_bar_x.append($('<div class="task-gantt-load-duration">'+duration_.h+'</div>'));
                            if (duration_.m !== "00") {
                                load_bar_x.append($('<div class="task-gantt-load-duration-m">' + duration_.m + '</div>'));

                            }
                        }


                        load_bar_x.css({"left": left_point + "px"});
                        load_bar_x.css({"width": bar_W + "px"});

                        $(rowdata).append(load_bar_x);
                    });

                }

            });

        }

    }

});

return {
    ResLevelWidget: GanttTimeLineResLevel


}

});