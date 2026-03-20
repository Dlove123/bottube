# BoTTube OEmbed Protocol - #528 (10 RTC)

class OEmbedProtocol:
    def __init__(self):
        self.providers = []
    
    def add_provider(self, url, format):
        self.providers.append({'url': url, 'format': format})
        return {'status': 'added', 'url': url}
    
    def get_providers(self):
        return self.providers

if __name__ == '__main__':
    oembed = OEmbedProtocol()
    oembed.add_provider('https://bottube.ai', 'json')
    print(oembed.get_providers())
