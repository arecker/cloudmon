import os

import CloudFlare
import yaml


cloudflare = CloudFlare.CloudFlare()


class Record(object):
    def __init__(self, zone):
        self.zone_id = cloudflare.zones.get(params={'name': zone})[0]['id']

    def __repr__(self):
        return 'Record <{} ({})>'.format(self.name, self.type)

    @classmethod
    def from_config(cls, zone, config):
        record = cls(zone)
        record.name = config['name']
        record.type = config['type']
        record.content = config['content']
        record.proxied = config.get('proxied', False)
        return record.populate()

    def as_search_params(self):
        return {
            'name': self.name,
            'type': self.type
        }

    def as_params(self):
        result = self.as_search_params()
        result['content'] = self.content
        result['proxied'] = self.proxied
        return result


    def exists(self):
        return any([
            record for record in cloudflare.zones.dns_records.get(self.zone_id)
            if self.name == record['name'] and self.type == record['type']
        ])

    def populate(self):
        if self.exists():
            self.id = cloudflare.zones.dns_records.get(
                self.zone_id,
                params=self.as_search_params()
            )[0]['id']
        else:
            self.id = None
        return self

    def apply(self):
        if self.id:
            cloudflare.zones.dns_records.put(self.zone_id, self.id, data=self.as_params())
        else:
            cloudflare.zones.dns_records.post(self.zone_id, data=self.as_params())


def main():
    here = os.path.dirname(os.path.realpath(__file__))
    config = yaml.load(open(os.path.join(here, 'config.yml')))
    for zone, info in config.items():
        config_records = map(
            lambda c: Record.from_config(zone, c),
            info.get('records', [])
        )
        for record in config_records:
            record.apply()
