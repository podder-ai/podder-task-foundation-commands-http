import mimetypes
import shutil
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, Response
from fastapi.responses import StreamingResponse
from podder_task_foundation.context import Context
from podder_task_foundation.objects.object import Object
from podder_task_foundation.payload import Payload
from podder_task_foundation.objects import factory_from_object
from podder_task_foundation.process_executor import ProcessExecutor
from starlette.datastructures import FormData, UploadFile


class ProcessHandler(object):
    def handle(self, context: Context, name: str, files: FormData,
               output_name: Optional[str]) -> Response:
        processes = context.processes
        if name not in processes:
            raise HTTPException(status_code=404,
                                detail="Process {} not found".format(name))
        _input = self._create_payload_from_request(context, files)
        process_executor = ProcessExecutor(mode=context.mode,
                                           config_path=str(
                                               context.config.path.absolute()),
                                           verbose=context.verbose,
                                           debug_mode=context.debug_mode)

        output = process_executor.execute(
            name,
            input_payload=_input,
        )

        return self._create_response_from_payload(context, output, output_name)

    @staticmethod
    def _create_payload_from_request(context: Context,
                                     files: FormData) -> Payload:
        _input = Payload()
        for name, data in files.items():
            if isinstance(data, UploadFile):
                data = [data]
            if not isinstance(data, list):
                continue
            for file in data:
                if isinstance(file, UploadFile):
                    extension = mimetypes.guess_extension(file.content_type)
                    original_path = Path(file.filename)
                    file_name = original_path.name
                    if original_path.suffix != extension:
                        file_name = file_name + extension
                    copied_path = context.file.temporary_directory.get(
                        file_name)
                    with copied_path.open("wb") as destination:
                        shutil.copyfileobj(file.file, destination)
                    _input.add_file(file=copied_path, name=name)
                else:
                    _object = factory_from_object(file)
                    _input.add(_object, name=name)

        return _input

    def _create_response_from_payload(self, context: Context, output: Payload,
                                      output_name: Optional[str]) -> Response:
        _object = None
        if output_name is not None:
            _object = output.get(output_name)
            if _object is None:
                keys = output.keys()
                key_list = ",".join(keys)
                raise HTTPException(
                    status_code=400,
                    detail=
                    "Output {} not found. Result includes the following keys: {}"
                    .format(output_name, key_list))

        if _object is None:
            if len(output) == 0:
                return Response({
                    "status": "success",
                    "message": "no output"
                },
                                media_type='application/json')

            _object = self._decide_response(output)
            if _object is None:
                return Response({
                    "status": "success",
                    "message": "no output"
                },
                                media_type='application/json')

        path = self._create_file_response(context, _object)

        file_handle = open(path, mode="rb")
        return StreamingResponse(file_handle,
                                 media_type=mimetypes.guess_type(str(path))[0])

    @staticmethod
    def _decide_response(output: Payload) -> Optional[Object]:
        if len(output) == 1:
            return output.all()[0]

        target_object = output.get(object_type=["dictionary", "array"])
        if target_object:
            return target_object

        target_object = output.get(object_type=["image", "pdf"])
        if target_object:
            return target_object

        if len(output) > 1:
            return output.all()[0]

        return None

    @staticmethod
    def _create_file_response(context: Context, _object: Object) -> Path:
        extension = _object.default_extension
        temporary_file = context.file.get_temporary_file(_object.name +
                                                         extension)
        context.logger.info("{} to {}".format(_object.name,
                                              str(temporary_file)))
        success = _object.save(temporary_file)
        context.logger.info("Success: {}".format(temporary_file.exists()))
        if not success:
            raise HTTPException(status_code=500,
                                detail="Could not save Output {} to {}".format(
                                    _object.name, temporary_file.name))

        return temporary_file
