from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.config.container_config import BUCKET_NAME
from app.utils import container_util, s3_util
from app.model.user import User
from app.model.container import Container
from flask_restx import Namespace, Resource, fields

ns = Namespace(
    name='container',
    description='컨테이너 관련 API'
    )

class _Schema():
    post_fields = ns.model('컨테이너 생성시 필요 데이터', {
        'name': fields.String(description='Container Name', example='test container 1') ,
        'description': fields.String(description='Container Description', example='Container for tag management'),
        'domain': fields.String(description='Domain of the Container', example='https://www.samsung.com')
    })

    basic_fields = ns.model('컨테이너 기본 정보', {
        'id': fields.Integer(description='Container ID', example=1),
        'name': fields.String(description='Container Name', example='test container 1'),
    })

    detail_fields = ns.inherit('컨테이너 상세 정보', basic_fields, {
        'domain': fields.String(description='Domain of the Container', example='https://www.samsung.com/'),
        'description': fields.String(description='Container Description', example='Container for tag management')
    })

    msg_fields = ns.model('상태 코드에 따른 설명', {
        'msg': fields.String(description='상태 코드에 대한 메세지', example='ok')
    })

    container_list = fields.List(fields.Nested(basic_fields))


@ns.route('/list')
class ContainerList(Resource):
    
    @ns.response(200, '컨테이너 리스트 조회 성공', _Schema.container_list)
    def get(self):
        """현재 회원의 컨테이너 리스트를 가져옵니다."""
        containers = User.get_containers(get_jwt_identity())
        response = [
            {
                "id": container.id,
                "name": container.name
            }
            for container in containers
        ]
        
        return response, 200


@ns.route('')
class ContainerCreate(Resource):
    @ns.expect(_Schema.post_fields)
    @ns.response(201, '컨테이너 생성 성공', _Schema.msg_fields)
    @jwt_required()
    def post(self):
        """새 컨테이너를 추가합니다."""
        body = request.json
        name = body['name']
        domain = body['domain']
        desc = body['description']

        Container.save(name=name, domain=domain, description=desc) 

        return {'msg':'ok'}, 201
    

@ns.route('/<int:container_id>')
@ns.doc(params={'container_id': '컨테이너의 id'})
class ContainerManage(Resource):
    
    @ns.response(200, "컨테이너 정보 조회 성공", _Schema.detail_fields)
    def get(self, container_id):
        """container_id와 일치하는 컨테이너의 상세 정보를 가져옵니다."""
        container = Container.get(container_id)
        response = {
            "id" : container.id,
            "name" : container.name,
            "domain" : container.domain,
            "description" : container.description
        }

        return response, 200

    
    @ns.expect(200, "새로운 컨테이너 데이터", _Schema.post_fields)
    @ns.response(200, '컨테이너 정보 수정 성공', _Schema.msg_fields)
    def put(self, container_id):
        """container_id와 일치하는 컨테이너의 정보를 수정합니다."""
        data = request.json
        name = data['name']
        domain = data['domain']
        desc = data['description']

        container = Container.get(container_id)
        container.update(name, domain, desc)

        return jsonify({"status": "ok"}), 200


    
    @ns.response(201, '컨테이너 삭제 성공', _Schema.msg_fields)
    def delete(self, container_id):
        """container_id와 일치하는 컨테이너를 삭제합니다."""
        user_id = get_jwt_identity()
        Container.delete(user_id, container_id)

        return jsonify({"status": "ok"}), 200
