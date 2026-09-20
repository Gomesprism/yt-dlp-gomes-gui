import json

from yt_dlp.gui import DownloadHistory


def test_download_history_persists_entries(tmp_path):
    path = tmp_path / 'history.json'
    history = DownloadHistory(path)
    entry = history.add(
        title='Vídeo de teste', url='https://example.com/video', location=tmp_path / 'videos',
        media_type='Vídeo', format_name='MP4 compatível')

    assert entry['title'] == 'Vídeo de teste'
    assert json.loads(path.read_text(encoding='utf-8'))[0]['location'] == str(tmp_path / 'videos')
    assert DownloadHistory(path).entries[0]['url'] == 'https://example.com/video'