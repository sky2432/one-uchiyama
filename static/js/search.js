const limitedHight = 80; // 実際に制限する高さ（px）

$(function () {
  // 画面表示時に実行する
  limitNumberOfWordsShownIfOverFlow();

  /**
   * 単語バッジを押したとき、Spotifyプレイヤーに開始時間を設定する
   * 開始時間またはSpotifyプレイヤーがない時は何もしない
   */
  $('.word-badge').click(function () {
    const startTime = $(this).find('.start-time').text();
    const $spotifyPlayer = $(this).parents('.words-wrap').prevAll('.radio-info').find('.spotify-player');
    if (!startTime || !$spotifyPlayer) {
      return;
    }
    const src = $spotifyPlayer.attr('src');
    const keyword = '&t='; // 開始時間の指定箇所
    const baseUrl = src.substring(0, src.indexOf(keyword));
    const urlWithStartTime = baseUrl + keyword + startTime;
    $spotifyPlayer.attr('src', urlWithStartTime)
  })

  /**
   * もっと見る・閉じるボタンを押したとき
   * 単語の全表示・一部非表示を切り替える
   */
  $('input[id^=switch]').change(function () {
    if ($(this).prop('checked')) { // もっと見る
      $(this).nextAll('.words').height('auto');
    } else { // 閉じる
      $(this).nextAll('.words').height(limitedHight);
    }
  })
})

/**
 * 単語が溢れているとき表示している単語数を制限する
 */
function limitNumberOfWordsShownIfOverFlow() {
  const maxHeight = 120; // 単語が溢れている場合に制限するように、実際に制限する高さより余分のある高さにしている
  $('.words').each(function () {
    if ($(this).height() >= maxHeight) {
      // styleを指定すると既存のcssが無効になるのでtailwindのclass名を付与している
      $(this).height(limitedHight);
      $(this).nextAll('.view-more-btn').css('display', 'block');
    }
  });
}