from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import json

from app.model.medium import Medium, PlatformList
from app.model.container import Container
from flask_restx import Namespace, Resource, fields, reqparse

ns = Namespace(name='medium', description='매체 관련 API', path='/')

class _Schema():

    platform_fields = ns.model('플렛폼 기본 정보', {
        'name': fields.String(description = "Platform name", example='Google Analytics')
    })

    post_fields = ns.model('매체 생성 시 필요 데이터', {
        'platform_name': fields.String(description = "Platform name in platform list", example='카카오'),
        'tracking_list': fields.List(fields.String(description='tracking ID', example='G123456'))
    })

    put_fields = ns.model('매체 수정 시 필요 데이터', {
        'tracking_list': fields.List(fields.String(description='tracking ID', example='G123456'))
    })

    basic_fields = ns.model('매체 기본정보', {
        'platform_name': fields.String(description='platform name', example='GA')
    })

    detail_fields = ns.inherit('매체 상세정보', basic_fields, {
        'tracking_list': fields.List(fields.String(description='tracking ID', example='G123456'))
    })

    medium_list = fields.List(fields.Nested(basic_fields))

    platform_list = fields.List(fields.Nested(platform_fields))

    msg_fields = ns.model('상태 코드에 따른 설명', {
        'msg': fields.String(description='상태 코드에 대한 메세지', example='처리 내용')
    })
    

@ns.route('/containers/platforms')
class GetPlatformList(Resource):
    @ns.response(200, '매체 플랫폼 리스트 조회 성공', _Schema.platform_list)
    def get(self):
        """서비스에서 사용가능한 플랫폼 리스트를 가져옵니다."""
        platforms = PlatformList.get_all()
        response = [
            {
                "name": platform.name
            }
            for platform in platforms
        ]
        return response, 200


@ns.route('/containers/<string:container_domain>/mediums')
class MediumListOrCreate(Resource):

    @ns.response(200, '매체 리스트 조회 성공', _Schema.medium_list)
    def get(self, container_domain):
        """현재 컨테이너의 매체 리스트를 가져옵니다."""
        mediums = Container.get_mediums(container_domain)
        response = [
            {
                'platform_name': PlatformList.get_name(medium.platform_id)
            }
            for medium in mediums
        ]
        return response, 200
    

    @ns.expect(_Schema.post_fields)
    @ns.response(201, '컨테이너에 매체 추가 성공', _Schema.msg_fields)
    @ns.response(400, '컨테이너에 매체 추가 실패', _Schema.msg_fields)
    def post(self, container_domain):
        """현재 컨테이너에 매체 정보를 추가합니다"""
        body = request.json
        platform_name = body['platform_name']
        tracking_list = body['tracking_list']

        medium = Medium.save(container_domain, platform_name, tracking_list)

        if not medium:
            return {'msg':'컨테이너 내에 동일한 이름의 매체가 이미 존재합니다.'}, 400
        
        return {'msg':'ok'}, 201


@ns.route('/containers/<string:container_domain>/mediums/<string:platform_name>')
@ns.doc(params={'container_domain': '컨테이너 도메인', 'platform_name': '플랫폼 이름'})
class MediumManage(Resource):

    @ns.response(200, "매체 정보 조회 성공", _Schema.detail_fields)
    def get(self, container_domain, platform_name):
        """특정 컨테이너의 한 플랫폼에 대한 매체의 상세정보를 가져옵니다"""
        medium = Medium.get_by_container_and_platform(container_domain, platform_name)
        response = {
            "tracking_list": medium.tracking_list,
        }
        return response, 200
    
    @ns.expect(200, "새로운 매체 데이터", _Schema.put_fields)
    @ns.response(200, "매체 tracking_list 수정 성공", _Schema.msg_fields)
    def put(self, container_domain, platform_name):
        """특정 컨테이너의 한 플랫폼에 대한 매체의 tracking_id 데이터를 수정합니다"""
        body = request.json
        tracking_list = body['tracking_list']
        medium = Medium.get_by_container_and_platform(container_domain, platform_name)
        medium.update_tracking_list(tracking_list)
        return {"msg": "ok"}, 200
    
    @ns.response(200, "매체 데이터 삭제 성공", _Schema.msg_fields)
    def delete(self, container_name, medium_name):
        """특정 컨테이너의 한 플랫폼에 대한 매체의 엔티티를 삭제합니다"""
        Medium.delete_by_container_and_platform(container_name ,medium_name)
        return {"msg": "ok"}, 200

