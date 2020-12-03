if (!window.dash_clientside) {
     window.dash_clientside = {}
 }

window.dash_clientside.clientside = {

    figure: function (fig_dict, title) {

        if (!fig_dict) {
            throw "Figure data not loaded, aborting update."
        }

        // Copy the fig_data so we can modify it
        // Is this required? Not sure if fig_data is passed by reference or value
        fig_dict_copy = {...fig_dict};

        fig_dict_copy["layout"]["title"] = title;

        return fig_dict_copy

    },

}