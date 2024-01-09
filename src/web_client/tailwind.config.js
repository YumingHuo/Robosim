module.exports = {
  content: ["./**/*.{html,js}"],
  corePlugins: { container: false },
  theme: {
    extend: {
      gridRowStart: {
        8: "8",
        9: "9",
        10: "10",
        11: "11",
        12: "12",
      },
    },
  },
  plugins: [],
  saveList: ['logWindow_dark', 'body_dark', 'version_dark', 'add_box_dark', 'remove_box_dark', 'north_dark', 'south_dark', 'east_dark', ' west_dark', 'up_dark', ' down_dark', 'camera_preset_front_dark', 'camera_preset_top_dark', 'camera_preset_back_dark', 'upload_CSV_dark', 'download_CSV_dark', 'clear_all_boxes_dark','leaderboard_dark','access_dark','release_dark','body_dark','img_dark']
};
