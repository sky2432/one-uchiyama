$(function () {
  /**
   * 単語バッジを押したとき、Spotifyプレイヤーに開始時間を設定する
   */
  $('.word-badge').click(function () {
    const startTime = $(this).find('.start-time').text();
    if (!startTime) return;
    const $spotifyPlayer = $(this).parent().prev().find('.spotify-player');
    const src = $spotifyPlayer.attr('src');
    const keyword = '&t=';
    const baseUrl = src.substring(0, src.indexOf(keyword));
    const urlWithStartTime = baseUrl + keyword + startTime;
    $spotifyPlayer.attr('src', urlWithStartTime)
  })
})