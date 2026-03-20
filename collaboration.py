# Creator Collaboration - #507 (25 RTC)
class Collaboration:
  def co_upload(s, u1, u2): return {'users': [u1,u2], 'status': 'uploaded'}
  def duet(s, v1, v2): return {'videos': [v1,v2], 'type': 'duet'}
  def share_revenue(s, u1, u2, amt): return {'split': amt/2, 'users': [u1,u2]}
