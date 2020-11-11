import numpy as np
import pixelengine
import sys
import traceback


class Backend:
    """
    Class declaration for backends
    """

    def __init__(self, name, context, backend):
        """
        :param name: Name of Backend
        :param context: Context name for backend
        :param contextclass: Context class name for backend
        :param backend: Backend name
        :param backendclass: Backend class
        """
        self.name = name
        self.context = context[0]
        self.backend = backend[0]
        self.contextclass = context[1]
        self.backendclass = backend[1]


# iterate over backend libraries that might or might not be available
backends = [
    Backend('SOFTWARE', ['softwarerendercontext', 'SoftwareRenderContext'],
            ['softwarerenderbackend', 'SoftwareRenderBackend']),
    Backend('GLES2', ['eglrendercontext', 'EglRenderContext'],
            ['gles2renderbackend', 'Gles2RenderBackend']),
    Backend('GLES3', ['eglrendercontext', 'EglRenderContext'],
            ['gles3renderbackend', 'Gles3RenderBackend'])
]

valid_backends = []
for backend in backends:
    try:
        if backend.context not in sys.modules:
            contextlib = __import__(backend.context)
        if backend.backend not in sys.modules:
            backendlib = __import__(backend.backend)
    except RuntimeError:
        pass
    else:
        backend.context = getattr(contextlib, backend.contextclass)
        backend.backend = getattr(backendlib, backend.backendclass)
        valid_backends.append(backend)

backends = valid_backends


def get_backends(back_end):
    """
    Method to get backend render and context
    :param back_end: Input backend given by user
    :return: backend renderer and context
    """
    for b_end in backends:
        if b_end.name == back_end:
            return b_end.backend(), b_end.context()
    return None


class ISyntaxParser:
    def __init__(self, slide_path):

        self.render_backend, self.render_context = get_backends("SOFTWARE")

        self.pe = pixelengine.PixelEngine(self.render_backend, self.render_context)
        self.pe_input = self.pe["in"]
        self.pe_input.open(slide_path)

    def slide_properties(self):
        """
        Properties related to input file are used in this method
        :return: Output of file properties
        """
        props = {
            'pixel_engine': {
                'version': self.pe.version,
            },
            'slide': {
                'barcode': self.pe_input.barcode,
                'created': self.pe_input.acquisition_datetime,
                'num_images': self.pe_input.num_images,
                'last_calibration': {
                    'date': self.pe_input.date_of_last_calibration,
                    'time': self.pe_input.time_of_last_calibration,
                },
                'device': {
                    'manufacturer': self.pe_input.manufacturer,
                    'model': self.pe_input.model_name,
                    'serial_number': self.pe_input.device_serial_number,
                }
            }
        }
        if self.pe_input.derivation_description:
            props['slide']['derivation_description'] = self.pe_input.derivation_description
        if self.pe_input.software_versions:
            props['slide']['software_version'] = self.pe_input.software_versions
        return props

    def region_pixel_data(self, x_start, y_start, width, height, level=0):
        resp = {}

        def width_height_calculation(_x_start, _x_end, _y_start, _y_end, _dim_ranges):
            """
            As the input Patch size is from User which is at Level 0 representation.
            Derive Patch Size for the given Level (it defines the output patch image size too)
            :param _x_start: Starting X coordinate
            :param _x_end: Ending X coordinate
            :param _y_start: Starting Y coordinate
            :param _y_end: Ending Y coordinate
            :param _dim_ranges: Dimension ranges
            :return: patch_width, patch_height
            """
            try:
                # View Range is defined as a closed set i.e. the start and end index is inclusive
                # For example, for startIndex = 0 and endIndex = 511, the size is 512
                _patch_width = int(1 + (_x_end - _x_start) / _dim_ranges[0][1])
                _patch_height = int(1 + (_y_end - _y_start) / _dim_ranges[1][1])
                return _patch_width, _patch_height
            except RuntimeError:
                traceback.print_exc()

        def extract_patch(_view, _region):
            """
            Method to calculate pixel buffer size, patch width, patch height
            :param _view: Source view object
            :param _region: Region
            :return: pixel_buffer_size, file_name, patch_width, patch_height
            """
            _x_start, _x_end, _y_start, _y_end, _level = _region.range
            _dim_ranges = _view.dimension_ranges(_level)
            _patch_width, _patch_height = width_height_calculation(_x_start, _x_end,
                                                                   _y_start, _y_end,
                                                                   _dim_ranges)
            # Calculate patch image size for writting to disk
            # 3 is samples per pixels for RGB
            # 4 is samples per pixels for RGBA
            _pixel_buffer_size = _patch_width * _patch_height * 4
            return _pixel_buffer_size, _patch_width, _patch_height

        try:
            view = self.pe_input["WSI"].source_view
            truncationlevel = {0: [0, 0, 0]}
            view.truncation(False, False, truncationlevel)
            # Querying number of derived levels in an iSyntax file
            num_levels = view.num_derived_levels + 1
            x_end = x_start + width
            y_end = y_start + height
            view_ranges = []
            view_range = [x_start, (x_end - (2 ** level)), y_start, (y_end - (2 ** level)),
                          level]
            view_ranges.append(view_range)
            data_envelopes = view.data_envelopes(level)
            regions = view.request_regions(
                view_ranges,
                data_envelopes,
                False,
                [0, 0, 0, 0],
                self.pe.BufferType(1)
            )
            region = regions[0]
            pixel_buffer_size, patch_width, patch_height = extract_patch(view, region)
            pixels = np.empty(int(pixel_buffer_size), dtype=np.uint8)
            region.get(pixels)
            image_width = int(int(width) / max([1, int(level) * 2]))
            image_height = int(int(height) / max([1, int(level) * 2]))
            pixels = np.reshape(pixels, (image_width, image_height, 4))
            resp['pixels'] = pixels.tolist()
            resp['success'] = True
            return resp
        except:
            resp['success'] = False
            resp['error'] = traceback.format_exc()
            return resp
