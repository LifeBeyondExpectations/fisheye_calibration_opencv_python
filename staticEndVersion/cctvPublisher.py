#!/usr/bin/env python

from __future__ import print_function
import numpy as np
import cv2

from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError

import rospy
import roslib

import pickle
from tempfile import TemporaryFile

import glob
import os


#flag
flag_subscribe_new_image_not_load_old_image = 1
flag_publish_calibrated_image = 1


flag_load_calibrated_result = 1
flag_load_detected_result = 0
flag_fisheye_calibrate = 1
flag_save_image_onlyWhichDetectCheckeboard = 1
flag_show_image = 1


#parameter
ROS_TOPIC = 'jaesung_lens_camera/image_color'
    #'jaesung_lens_camera/image_color'
path_image_database = "video_francois_lens/*.png"
save_video_to_the_path = "video_francois_lens/"
nameOf_pickle_Checkerboard_Detection = 'result/detection_result_francois_171021_1620_delete_image'
#"result/addedImages_kiback_advice_included.pickle"
nameof_pickel_calibrated_result = "calib_result_JS_fisheye.pickle"
#fisheye-calibration-opencv-python-ROS/staticEndVersion/

fileList = []
num_of_image_in_database = 1000
count = 0
mybalance = 0

class calibration:
    # you must check the checkboard which you would like to use for the calibration
    # if (9, 7) it means there are 10(=9+1) pactches in row, 8(=7+1) patches in column
    CHECKERBOARD = (9, 7)  # (8, 8)

    # Arrays to store object points and image points from all the images.
    objpoints = []  # 3d point in real world space
    imgpoints = []  # 2d points in image plane.
    # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
    objp = []

    flag_calibratedResult_save = 1
    flag_get_undistort_param = 1
    height = 0
    width = 0

    def __init__(self):
        # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
        self.objp = np.zeros((1, self.CHECKERBOARD[0] * self.CHECKERBOARD[1], 3), np.float32)
        self.objp[0, :, :2] = np.mgrid[0:self.CHECKERBOARD[0], 0:self.CHECKERBOARD[1]].T.reshape(-1, 2)
        # print('self.objp is')
        # print(self.objp)

    def detectCheckerBoard(self, frame):
        # Our operations on the frame come here
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # https://docs.opencv.org/trunk/d9/d0c/group__calib3d.html#ga93efa9b0aa890de240ca32b11253dd4a
        ret, corners = cv2.findChessboardCorners(image=gray,
                                                 patternSize=self.CHECKERBOARD,
                                                 flags=(cv2.CALIB_CB_ADAPTIVE_THRESH+cv2.CALIB_CB_NORMALIZE_IMAGE))

        # If found, add object points, image points (after refining them)
        if ret == True:
            print(">> detected the checkerboard")

            # Save images if wanted
            if flag_subscribe_new_image_not_load_old_image == 1 and flag_save_image_onlyWhichDetectCheckeboard == 1:
                cv2.imwrite(save_video_to_the_path + (str((count + 0)) + '.png'), frame)

            # https://docs.opencv.org/3.0-beta/modules/imgproc/doc/feature_detection.html#void cornerSubPix(InputArray image, InputOutputArray corners, Size winSize, Size zeroZone, TermCriteria criteria)
            corners2 = cv2.cornerSubPix(image=gray,
                                        corners=corners,
                                        winSize=(11, 11),
                                        zeroZone=(-1, -1),
                                        criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))

            self.imgpoints.append(corners2)
            self.objpoints.append(self.objp)

            # Draw and display the corners
            frame = cv2.drawChessboardCorners(image=frame, patternSize=self.CHECKERBOARD, corners=corners2, patternWasFound=ret)

        # Display the resulting frame
        cv2.namedWindow('frame')
        cv2.imshow('frame', frame)
        cv2.waitKey(1)

    def saveVarInDetection(self):
        with open(nameOf_pickle_Checkerboard_Detection, 'w') as f:
            pickle.dump([self.objpoints, self.imgpoints, self.width, self.height], f)

    def loadVarInDetection(self):
        with open(nameOf_pickle_Checkerboard_Detection) as f:
            self.objpoints, self.imgpoints, self.width, self.height = pickle.load(f)

            # check the result
            tmp = np.array(self.objpoints)
            print("shape of objpoints is ", tmp.shape)

            tmp = np.array(self.imgpoints)
            print("shape of imgpoints is ", tmp.shape)

            print("width is ", self.width, "height is ", self.height)

    def startCalibration(self):
        global mybalance

        if flag_fisheye_calibrate == 0:
            self.ret, self.camera_matrix, self.distCoeffs, self.rvecs, self.tvecs = cv2.calibrateCamera(
                self.objpoints, self.imgpoints, (self.width, self.height), None, None)

            # check the result of calibration
            print("self.camera_matrix=np.array(" + str(self.camera_matrix.tolist()) + ")")
            print("self.distCoeffs=np.array(" + str(self.distCoeffs.tolist()) + ")")

            # https://docs.opencv.org/3.0-beta/modules/calib3d/doc/camera_calibration_and_3d_reconstruction.html#getoptimalnewcameramatrix
            self.new_camera_matrix, self.roi = cv2.getOptimalNewCameraMatrix(self.camera_matrix,
                                                                             self.distCoeffs,
                                                                             (self.width, self.height), mybalance,
                                                                             (self.width, self.height))
            print("self.roi is ", self.roi)

            ## self.roi or (self.width, self.height) ??
            self.map1, self.map2 = cv2.initUndistortRectifyMap(self.camera_matrix, self.distCoeffs, np.eye(3),
                                                               self.new_camera_matrix,
                                                               (self.width, self.height),
                                                               cv2.CV_16SC2)

        else:
            # self.ret, self.camera_matrix, self.distCoeffs, self.rvecs, self.tvecs = cv2.fisheye.calibrate(self.objpoints, self.imgpoints, (self.width, self.height), None, None)
            # you should write all the cv2.fisheye.CALIB_..3 things .. then it works



            # # The result is same with originally works
            # self.ret, self.camera_matrix, self.distCoeffs, self.rvecs, self.tvecs = cv2.fisheye.calibrate(
            #     self.objpoints, self.imgpoints, (self.width, self.height), None, None, None, None,
            #     cv2.fisheye.CALIB_RECOMPUTE_EXTRINSIC + cv2.fisheye.CALIB_FIX_SKEW,
            #     (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-6))

            # self.ret, self.camera_matrix, self.distCoeffs, self.rvecs, self.tvecs = cv2.fisheye.calibrate(
            #     self.objpoints, self.imgpoints, (self.width, self.height), None, None, None, None,
            #     cv2.fisheye.CALIB_RECOMPUTE_EXTRINSIC,
            #     (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-6))

            # No good results at all
            # self.ret, self.camera_matrix, self.distCoeffs, self.rvecs, self.tvecs = cv2.fisheye.calibrate(
            #     self.objpoints, self.imgpoints, (self.width, self.height), None, None, None, None,
            #     cv2.fisheye.CALIB_CHECK_COND,
            #     (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-6))

            # No good results at all
            # self.ret, self.camera_matrix, self.distCoeffs, self.rvecs, self.tvecs = cv2.fisheye.calibrate(
            #     self.objpoints, self.imgpoints, (self.width, self.height), None, None, None, None,
            #     cv2.fisheye.CALIB_FIX_INTRINSIC,
            #     (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-6))

            # Does not work at all
            # self.ret, self.camera_matrix, self.distCoeffs, self.rvecs, self.tvecs = cv2.fisheye.calibrate(
            #     self.objpoints, self.imgpoints, (self.width, self.height), None, None)

            # originally works
            # self.ret, self.camera_matrix, self.distCoeffs, self.rvecs, self.tvecs = cv2.fisheye.calibrate(
            #     self.objpoints, self.imgpoints, (self.width, self.height), None, None, None, None,
            #     cv2.fisheye.CALIB_RECOMPUTE_EXTRINSIC + cv2.fisheye.CALIB_CHECK_COND + cv2.fisheye.CALIB_FIX_SKEW,
            #     (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-6))

            # originally works
            N_OK = len(self.objpoints)
            self.camera_matrix = np.zeros((3, 3))
            self.distCoeffs = np.zeros((4, 1))
            self.rvecs = [np.zeros((1, 1, 3), dtype=np.float64) for i in range(N_OK)]
            self.tvecs = [np.zeros((1, 1, 3), dtype=np.float64) for i in range(N_OK)]
            self.ret, _, _, _, _ = cv2.fisheye.calibrate(
                objectPoints=self.objpoints,
                imagePoints=self.imgpoints,
                image_size=(self.width, self.height),
                K=self.camera_matrix,
                D=self.distCoeffs,
                rvecs=None,#self.rvecs,
                tvecs=None,#self.tvecs,
                flags=(cv2.fisheye.CALIB_RECOMPUTE_EXTRINSIC),#+ cv2.fisheye.CALIB_FIX_SKEW), # +cv2.fisheye.CALIB_FIX_PRINCIPAL_POINT cv2.fisheye.CALIB_CHECK_COND
                criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, 1e-6))

            # check the result of calibration
            print('camera matrix is ')
            print(self.camera_matrix)
            # print('new camera Matrix is ')
            # print(self.new_camera_matrix)
            # print('self.rvecs is ')
            # print(self.rvecs)
            # print('self.tvecs is ')
            # print(self.tvecs)
            print('distort Coeffs is ')
            print(self.distCoeffs)
            print('RMS re-projection error is ', self.ret)
            print('balance is ', mybalance)
            print('fuck')

            # self.distCoeffs = np.zeros((4, 1))
            self.roi = [0,0,0,0]

            # check the result of calibration
            print('camera matrix is ')
            print(self.camera_matrix)
            # print('new camera Matrix is ')
            # print(self.new_camera_matrix)
            print('distort Coeffs is ')
            print(self.distCoeffs)
            # print('self.roi is ', self.roi)
            print('fuck2')

            self.new_camera_matrix = self.camera_matrix
            self.map1 = 0
            self.map2 = 0
            # self.new_camera_matrix = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(K=self.camera_matrix,
            #                                                                                 D=self.distCoeffs,
            #                                                                                 image_size=(self.width, self.height),
            #                                                                                 R=np.eye(3),
            #                                                                                 P=None,
            #                                                                                 balance=mybalance,
            #                                                                                 new_size=(self.width, self.height),
            #                                                                                 fov_scale=1.0
            #                                                                                 )
            # # check the result of calibration
            # print('camera matrix is ')
            # print(self.camera_matrix)
            # print('new camera Matrix is ')
            # print(self.new_camera_matrix)
            # print('distort Coeffs is ')
            # print(self.distCoeffs)
            #
            # # https://medium.com/@kennethjiang/calibrate-fisheye-lens-using-opencv-part-2-13990f1b157f
            # self.map1, self.map2 = cv2.fisheye.initUndistortRectifyMap(K=self.camera_matrix,
            #                                                            D=self.distCoeffs,
            #                                                            R=np.eye(3),
            #                                                            P=self.new_camera_matrix,
            #                                                            size=(self.width, self.height),
            #                                                            m1type=cv2.CV_32FC1)

        tmp = np.array(self.map1)
        print("self.map1 is ", tmp.shape)
        tmp = np.array(self.map2)
        print("self.map2 is ", tmp.shape)
        # http://opencv-users.1802565.n2.nabble.com/Re-what-is-CV-32FC1-td6684091.html
        # CV_<bit_depth>(S|U|F)C<number_of_channels>
        # bit_depth is number of bits per element in matrix.supported bit. depth are 8, 16, 32, and 84.
        # S = signed, U = unsigned, F = float
        # number_of_channels is of course number of channels, in term of matrix you can think of this as third dimension

        print("calibration complete")

    def saveVarAfterCalibration(self):

        if flag_fisheye_calibrate == 0:
            with open(nameof_pickel_calibrated_result, 'w') as f:
                pickle.dump([self.camera_matrix, self.distCoeffs, self.new_camera_matrix, self.width, self.height, self.roi, self.map1, self.map2], f)
            print('self.roi is', self.roi)
        else:
            with open(nameof_pickel_calibrated_result, 'w') as f:
                pickle.dump([self.camera_matrix, self.distCoeffs, self.new_camera_matrix, self.width, self.height, self.roi, self.map1, self.map2], f)

    def loadVarAfterCalibration(self):

        with open(nameof_pickel_calibrated_result) as f:
            self.camera_matrix, self.distCoeffs, self.new_camera_matrix, self.width, self.height, self.roi, self.map1, self.map2 = pickle.load(f)
            #for old data, erase self.roi, self.map1, self.map2

        print('camera matrix is ')
        print(self.camera_matrix)
        print('new camera Matrix is ')
        print(self.new_camera_matrix)
        print('distort Coeffs is ')
        print(self.distCoeffs)
        print('width, height is ', self.width, self.height)

    def undistort_imShow(self, frame):
        #print('shape of frames is ', frame.shape)
        #frame = cv2.resize(frame, (964, 1288), cv2.INTER_LINEAR)
        dim0 = frame.shape[:2][::-1]
        dim1 = dim0
        dim2 = dim1
        dim3 = tuple((np.array(dim1)*1).astype(int))
        displayDim = (640, 480) #tuple((np.array(frame.shape[:2][::-1]) / 2.5).astype(int))
        #print('dim3 is ', dim3, 'dim2 is ', dim2, 'dim1 is ', dim1)
        #print('shape of the tained images are ', (self.width, self.height))

        if flag_fisheye_calibrate == 0:

            # best
            # cv2.undistort : https://docs.opencv.org/3.1.0/da/d54/group__imgproc__transform.html#ga69f2545a8b62a6b0fc2ee060dc30559d
            # The function is simply a combination of initUndistortRectifyMap() (with unity R ) and remap() (with bilinear interpolation)
            # I cannot tell the difference between the two line below
            frame_with_new_camera_matrix = cv2.undistort(frame, self.new_camera_matrix, self.distCoeffs, None, None)
            frame_with_origin_camera_matrix = cv2.undistort(frame, self.camera_matrix, self.distCoeffs, None, None)

            # cv2.namedWindow('undistorted frame')
            #cv2.imshow('undistorted frame', frame_with_new_camera_matrix)



            # shit
            frame_with_remap = cv2.remap(frame, self.map1, self.map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
            #cv2.imshow('undistorted frame', frame_with_remap)

            # compare with distorted / undistorted
            # cv2.imshow('undistorted frame', np.concatenate((frame_with_new_camera_matrix, frame), axis=1))
            # compare with camera_matrixes
            # cv2.imshow('undistorted frame', np.concatenate((frame_with_new_camera_matrix, frame_with_origin_camera_matrix), axis=1))
            # test
            cv2.imshow('undistorted frame', np.concatenate((cv2.resize(frame_with_new_camera_matrix, (self.width, self.height), cv2.INTER_CUBIC),
                                                            cv2.resize(frame_with_origin_camera_matrix, (self.width, self.height), cv2.INTER_CUBIC),
                                                            cv2.resize(frame_with_remap, (self.width, self.height), cv2.INTER_CUBIC)
                                                            ),
                                                           axis=1))
            cv2.waitKey(1)

        elif flag_fisheye_calibrate == 1:

            if self.flag_get_undistort_param == 1:

                # self.new_camera_matrix = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(K=self.camera_matrix,
                #                                                                                 D=self.distCoeffs,
                #                                                                                 image_size=(self.width, self.height),
                #                                                                                 R=np.eye(3),
                #                                                                                 P=None,
                #                                                                                 balance=mybalance,
                #                                                                                 new_size=dim3#,fov_scale=1.0
                #                                                                                 )
                #
                # # https://medium.com/@kennethjiang/calibrate-fisheye-lens-using-opencv-part-2-13990f1b157f
                # self.map1, self.map2 = cv2.fisheye.initUndistortRectifyMap(K=self.camera_matrix,
                #                                                              D=self.distCoeffs,
                #                                                              R=np.eye(3),
                #                                                              P=self.camera_matrix,
                #                                                              size=dim3,
                #                                                              m1type=cv2.CV_32FC1)
                #
                #
                # # check the result of calibration
                # print('camera matrix is ')
                # print(self.camera_matrix)
                # print('new camera Matrix is ')
                # print(self.new_camera_matrix)
                # print('distort Coeffs is ')
                # print(self.distCoeffs)
                #
                self.flag_get_undistort_param = 0


            frame_undistorted_fisheye_camera_matrix = cv2.fisheye.undistortImage(frame, self.camera_matrix, self.distCoeffs, Knew=self.camera_matrix, new_size=dim0)#(self.width, self.height))
            # frame_undistorted_fisheye_remap_with_origin_camera_matrix = cv2.remap(src=frame,map1=self.map1,map2=self.map2,interpolation=cv2.INTER_LINEAR,borderMode=cv2.BORDER_DEFAULT)


            tmp = cv2.resize(cv2.rotate(frame_undistorted_fisheye_camera_matrix, cv2.ROTATE_90_CLOCKWISE), displayDim, cv2.INTER_LINEAR)
            if flag_show_image == 1:
                # cv2.imshow('jaesungLensFrame', np.concatenate((cv2.resize(frame_undistorted_fisheye_camera_matrix, displayDim, cv2.INTER_LINEAR),
                #                                          cv2.resize(frame_undistorted_fisheye_remap_with_origin_camera_matrix, displayDim, cv2.INTER_LINEAR),
                #                                          cv2.resize(frame, displayDim, cv2.INTER_LINEAR)),axis=1))
                #tmp = cv2.resize(frame_undistorted_fisheye_camera_matrix, displayDim, cv2.INTER_LINEAR)

                cv2.namedWindow('JS calibrated resuls')
                cv2.imshow('JS calibrated resuls', tmp)

            cv2.waitKey(1)
            return tmp
        else:
            print('error for <flag_fisheye_calibrate>')
            return None

class dataLoadType:

    singleImage_inst = []
    calibrate_inst = []
    flag_fisrt_didLoadVarDetection = 1
    flag_first_didLoadVarCalibration = 1
    flag_first_didHomography = 1

    def __init__(self, singleImage_inst, calibrate_inst):
        self.singleImage_inst = singleImage_inst
        self.calibrate_inst = calibrate_inst
        self.bridge = CvBridge()

    def subscribeImage(self):
        print('start to subscribe image')
        #rospy.init_node('dataLoadType', anonymous=True)
        self.rospySubImg = rospy.Subscriber('cctv_camera/image_color', Image, self.callback)
        #automatically go to the callback function : self.callback()

    def stopSubscribing(self):
        print('stop subscribing image')
        #self.image_sub.shutdown()
        self.rospySubImg.unregister()

    def loadImageInFiles(self):
        global fileList
        fileList = glob.glob(path_image_database)
        print('path_image_database is ', path_image_database)

        global num_of_image_in_database
        num_of_image_in_database = len(fileList)
        print('what is fileList', fileList, '\n')

        global count
        for i in fileList:
            count = count + 1
            print('The ', count, '-th image is under processing')
            self.singleImage_inst.saveImage(cv2.imread(i))

            self.wrapper()

    def publishImage(self):
        # http://wiki.ros.org/ROS/Tutorials/WritingPublisherSubscriber%28python%29
        print('start to publish cctv image')
        self.rospyPubImg = rospy.Publisher('cctv_camera/image_republished', Image, queue_size=10)
        #rospy.init_node('calibrated_JS_lens_fisheye', anonymous=True)
        rate = rospy.Rate(10)  # 10Hz


    def callback(self, data):
        #print('come to callback function')
        global count
        try:
            # parse message into image
            # bgr8: CV_8UC3, color image with blue-green-red color order and 8bit
            self.singleImage_inst.saveImage(self.bridge.imgmsg_to_cv2(data, "bgr8"))
            count = count + 1

            # cv2.imshow('subscriber check', self.singleImage_inst.imgData)
            # cv2.waitKey(1)

            # if you want to work asynchronously, edit the lines below
            global flag_publish_calibrated_image
            if flag_publish_calibrated_image == 1:
                self.wrapper()
            else:
                self.wrapper_homography(self.singleImage_inst.imgData)

        except CvBridgeError as e:
            print(e)

    def wrapper_homography(self, frame_cctv):
        frame_cctv = cv2.resize(cv2.rotate(frame_cctv, rotateCode=cv2.ROTATE_90_CLOCKWISE), (0, 0), fx=0.5, fy=0.5)
        if self.flag_first_didHomography == 1:

            # srcPoints_cctv = np.array([[121, 422], [197, 408], [265, 394], [322, 379],
            #                            [55, 479],  [151, 456], [239, 445], [312, 418], [374, 499],
            #                            [84, 535],  [198, 506], [298, 476],
            #                            [130, 618], [270, 567], [374, 523],
            #                                        [371, 657]])
            #
            # dstPoints_cctv = np.array([            [250, 250], [250, 200], [250, 150], [250, 100],
            #                            [200, 300], [200, 250], [200, 200], [200, 150], [200, 200],
            #                            [150, 300], [150, 250], [150, 200],
            #                            [100, 300], [100, 250], [100, 200],
            #                                        [50, 250]])

            srcPoints_cctv = np.array([[102, 234],   [182, 221],   [262, 218],
                                       [92, 266],  [185, 258],  [280, 249],
                                       [78, 313],  [188, 303], [300, 295],
                                       [60, 382],  [197, 374], [241,371],[285,366], [334, 360],
                                       [36, 492],   [210, 481], [377, 461], [515, 432],
                                       [16, 648],   [231, 643], [440, 600]])

            dstPoints_cctv = np.array([[250, 0],   [200, 0],   [150, 0],
                                       [250, 50],  [200, 50],  [150, 50],
                                       [250, 100], [200, 100], [150, 100],
                                       [250, 150], [200, 150], [184,150],[166,150],[150, 150],
                                       [250, 200], [200, 200], [150, 200], [100, 200],
                                       [250, 250], [200, 250], [150, 250]])

            srcPoints_cctv, dstPoints_cctv = np.array(srcPoints_cctv), np.array(dstPoints_cctv)
            self.homography_cctv, mask = cv2.findHomography(srcPoints=srcPoints_cctv, dstPoints=dstPoints_cctv, method=cv2.RANSAC)

            self.flag_first_didHomography = 0

        frame_homography_cctv = cv2.warpPerspective(frame_cctv, self.homography_cctv, (250, 250))
        # cv2.waitKey(1)

        global flag_show_image
        if flag_show_image == 1:
            # cv2.namedWindow('oroginal cctv frmae')
            # cv2.imshow('oroginal cctv frmae', frame_cctv)
            cv2.namedWindow('frame_homography_cctv results')
            cv2.imshow('frame_homography_cctv results', cv2.resize(frame_homography_cctv, (0, 0), fx=2, fy=2))
            #cv2.imshow('frame_homography_cctv results', cv2.flip(frame_homography_cctv, flipCode=-1))
            # cv2.imshow('frame_homography_cctv results', frame_homography_cctv)
            cv2.waitKey(1)

        try:
            self.rospyPubImg.publish(self.bridge.cv2_to_imgmsg(frame_homography_cctv, "bgr8"))
        except CvBridgeError as e:
            print(e)

    def wrapper(self):

        try:
            img_cctv = cv2.resize(cv2.rotate(self.singleImage_inst.imgData, rotateCode=cv2.ROTATE_90_CLOCKWISE), (0,0), fx=0.5, fy=0.5)
            self.rospyPubImg.publish(self.bridge.cv2_to_imgmsg(img_cctv, "bgr8"))

            global flag_show_image
            if flag_show_image == 1:
                cv2.imshow('cctv display', img_cctv)
                cv2.waitKey(1)
        except CvBridgeError as e:
            print(e)

class singleImageData:
    height = 0
    width = 0
    imgData = None
    imgCalibrated = None

    def saveImage(self, img):
        self.imgData = img
        self.height, self.width = self.imgData.shape[:2]

    def resize(self, ratio):
        #cv2.resize(self.imgData, )
        print('resize of the image completed')

if __name__ == "__main__":

    print("check the version opencv.")
    print(cv2.__version__)

    #global count
    count = 0

    singleImage_inst = singleImageData()
    calibrate_inst = calibration()
    dataLoadType_inst = dataLoadType(singleImage_inst, calibrate_inst)

    #global flag_subscribe_new_image_not_load_old_image
    try:
       if flag_subscribe_new_image_not_load_old_image == 1:
            # One python file for one init_node
            rospy.init_node('cctv_publisher', anonymous=True)

            dataLoadType_inst.subscribeImage()
            dataLoadType_inst.publishImage()

            rospy.spin()

    except KeyboardInterrupt:
        print("Shutting down")

    cv2.destroyAllWindows()






