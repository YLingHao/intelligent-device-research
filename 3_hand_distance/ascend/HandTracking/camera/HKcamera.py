import sys
import numpy as np
import cv2
import time

sys.path.append("/opt/MVS/Samples/aarch64/Python/MvImport")
from MvCameraControl_class import *


def Enum_device(tlayerType, deviceList):
    """
    ch:枚举设备 | en:Enum device
    nTLayerType [IN] 枚举传输层 ，pstDevList [OUT] 设备列表
    """
    ret = MvCamera.MV_CC_EnumDevices(tlayerType, deviceList)
    if ret != 0:
        print("enum devices fail! ret[0x%x]" % ret)
        sys.exit()

    if deviceList.nDeviceNum == 0:
        print("find no device!")
        sys.exit()

    print("Find %d devices!" % deviceList.nDeviceNum)

    for i in range(0, deviceList.nDeviceNum):
        mvcc_dev_info = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
        if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE:
            print("\ngige device: [%d]" % i)
            # 输出设备名字
            strModeName = ""
            for per in mvcc_dev_info.SpecialInfo.stGigEInfo.chModelName:
                strModeName = strModeName + chr(per)
            print("device model name: %s" % strModeName)
            # 输出设备ID
            nip1 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24)
            nip2 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16)
            nip3 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8)
            nip4 = (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff)
            print("current ip: %d.%d.%d.%d\n" % (nip1, nip2, nip3, nip4))
        # 输出USB接口的信息
        elif mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
            print("\nu3v device: [%d]" % i)
            strModeName = ""
            for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chModelName:
                if per == 0:
                    break
                strModeName = strModeName + chr(per)
            print("device model name: %s" % strModeName)

            strSerialNumber = ""
            for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chSerialNumber:
                if per == 0:
                    break
                strSerialNumber = strSerialNumber + chr(per)
            print("user serial number: %s" % strSerialNumber)


def enable_device(nConnectionNum):
    """
    设备使能
    :param nConnectionNum: 设备编号
    :return: 相机, 图像缓存区, 图像数据大小
    """
    # ch:创建相机实例 | en:Creat Camera Object
    cam = MvCamera()

    # ch:选择设备并创建句柄 | en:Select device and create handle
    # cast(typ, val)，这个函数是为了检查val变量是typ类型的，但是这个cast函数不做检查，直接返回val
    stDeviceList = cast(deviceList.pDeviceInfo[int(nConnectionNum)], POINTER(MV_CC_DEVICE_INFO)).contents

    ret = cam.MV_CC_CreateHandle(stDeviceList)
    if ret != 0:
        print("create handle fail! ret[0x%x]" % ret)
        sys.exit()

    # ch:打开设备 | en:Open device
    ret = cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
    if ret != 0:
        print("open device fail! ret[0x%x]" % ret)
        sys.exit()

    # ch:探测网络最佳包大小(只对GigE相机有效) | en:Detection network optimal package size(It only works for the GigE camera)
    if stDeviceList.nTLayerType == MV_GIGE_DEVICE:
        nPacketSize = cam.MV_CC_GetOptimalPacketSize()
        if int(nPacketSize) > 0:
            ret = cam.MV_CC_SetIntValue("GevSCPSPacketSize", nPacketSize)
            if ret != 0:
                print("Warning: Set Packet Size fail! ret[0x%x]" % ret)
        else:
            print("Warning: Get Packet Size fail! ret[0x%x]" % nPacketSize)

    # ch:设置触发模式为off | en:Set trigger mode as off
    ret = cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
    if ret != 0:
        print("set trigger mode fail! ret[0x%x]" % ret)
        sys.exit()
        
    

    # 从这开始，获取图片数据
    # ch:获取数据包大小 | en:Get payload size
    stParam = MVCC_INTVALUE()
    memset(byref(stParam), 0, sizeof(MVCC_INTVALUE))
    # MV_CC_GetIntValue，获取Integer属性值，handle [IN] 设备句柄
    # strKey [IN] 属性键值，如获取宽度信息则为"Width"
    # pIntValue [IN][OUT] 返回给调用者有关相机属性结构体指针
    # 得到图片尺寸，这一句很关键
    # payloadsize，为流通道上的每个图像传输的最大字节数，相机的PayloadSize的典型值是(宽x高x像素大小)，此时图像没有附加任何额外信息
    ret = cam.MV_CC_GetIntValue("PayloadSize", stParam)
    if ret != 0:
        print("get payload size fail! ret[0x%x]" % ret)
        sys.exit()

    nPayloadSize = stParam.nCurValue

    # ch:开始取流 | en:Start grab image
    ret = cam.MV_CC_StartGrabbing()
    if ret != 0:
        print("start grabbing fail! ret[0x%x]" % ret)
        sys.exit()
    #  返回获取图像缓存区。
    data_buf = (c_ubyte * nPayloadSize)()
    #  date_buf前面的转化不用，不然报错，因为转了是浮点型
    return cam, data_buf, nPayloadSize


def get_image(data_buf, nPayloadSize):
    """
    获取图像
    :param data_buf:
    :param nPayloadSize:
    :return: 图像
    """
    # 输出帧的信息
    stFrameInfo = MV_FRAME_OUT_INFO_EX()
    # void *memset(void *s, int ch, size_t n);
    # 函数解释:将s中当前位置后面的n个字节 (typedef unsigned int size_t )用 ch 替换并返回 s
    # memset:作用是在一段内存块中填充某个给定的值，它是对较大的结构体或数组进行清零操作的一种最快方法
    # byref(n)返回的相当于C的指针右值&n，本身没有被分配空间
    # 此处相当于将帧信息全部清空了
    memset(byref(stFrameInfo), 0, sizeof(stFrameInfo))

    # 采用超时机制获取一帧图片，SDK内部等待直到有数据时返回，成功返回0
    ret = cam.MV_CC_GetOneFrameTimeout(byref(data_buf), nPayloadSize, stFrameInfo, 1000)
    if ret == 0:
        pass
        #print("get one frame: Width[%d], Height[%d], nFrameNum[%d]" % (
        #    stFrameInfo.nWidth, stFrameInfo.nHeight, stFrameInfo.nFrameNum))
    else:
        print("no data[0x%x]" % ret)
    
    nRGBSize = stFrameInfo.nWidth * stFrameInfo.nHeight*3

    stConvertParam = MV_CC_PIXEL_CONVERT_PARAM()
    memset(byref(stConvertParam), 0, sizeof(stConvertParam))
    stConvertParam.nWidth = stFrameInfo.nWidth
    stConvertParam.nHeight = stFrameInfo.nHeight
    stConvertParam.pSrcData = data_buf
    stConvertParam.nSrcDataLen = stFrameInfo.nFrameLen
    stConvertParam.enSrcPixelType = stFrameInfo.enPixelType  
    stConvertParam.enDstPixelType = PixelType_Gvsp_RGB8_Packed 
    stConvertParam.pDstBuffer = (c_ubyte * nRGBSize)()
    stConvertParam.nDstBufferSize = nRGBSize

    ret = cam.MV_CC_ConvertPixelType(stConvertParam)
    #print(ret)
    if ret != 0:
        print ("convert pixel fail! ret[0x%x]" % ret)
        del data_buf
        sys.exit()

    #print("Convent OK")

    #data_buf = (c_ubyte * stConvertParam.nDstLen)()
    data_buf = (c_ubyte * stConvertParam.nDstLen)()
    memmove(byref(data_buf), stConvertParam.pDstBuffer, stConvertParam.nDstLen)


    image = np.asarray(data_buf)  # 将c_ubyte_Array转化成ndarray得到（3686400，）
    #print(len(data_buf))
    image = image.reshape((stFrameInfo.nHeight, stFrameInfo.nWidth, -1))  # 根据自己分辨率进行转化
    #print(image.shape)
    return image


def close_device(cam, data_buf):
    """
    关闭设备
    :param cam:
    :param data_buf:
    """
    # ch:停止取流 | en:Stop grab image
    ret = cam.MV_CC_StopGrabbing()
    if ret != 0:
        print("stop grabbing fail! ret[0x%x]" % ret)
        del data_buf
        sys.exit()

    # ch:关闭设备 | Close device
    ret = cam.MV_CC_CloseDevice()
    if ret != 0:
        print("close deivce fail! ret[0x%x]" % ret)
        del data_buf
        sys.exit()

    # ch:销毁句柄 | Destroy handle
    ret = cam.MV_CC_DestroyHandle()
    if ret != 0:
        print("destroy handle fail! ret[0x%x]" % ret)
        del data_buf
        sys.exit()

    del data_buf



def getPixelCoordinates():
    corner_coordinates = []
    image = None # 预定义
    while len(corner_coordinates) < 9:
        # time_start = time.time()
        
        image = get_image(data_buf, nPayloadSize)
        #print(image.shape)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        #print(image.shape)
        image = cv2.rotate(image, cv2.ROTATE_180)
        image = cv2.resize(image, dsize=(640, 480))
        # cv2.line(image,(90,0),(90,486),(0,0,255),3)
        
        
        # 设置棋盘格尺寸
        # board_size = (6, 8)
        board_size = (8, 11)

        # 创建棋盘格标定板对象
        calibration_board = np.zeros((np.prod(board_size), 3), np.float32)
        calibration_board[:, :2] = np.mgrid[0:board_size[0], 0:board_size[1]].T.reshape(-1, 2)

        # 查找棋盘格角点
        found, corners = cv2.findChessboardCorners(image, board_size, None)

        if found:
            # 输出角点坐标
            for corner in corners:
                x, y = corner[0]
                corner_coordinates.append((x, y))
                print("角点坐标：", x, y)

        for i, corner in enumerate(corner_coordinates):
            x, y = map(int, corner)
            cv2.circle(image, (x, y), 5, (0, 0, 255), -1)
            #cv2.putText(image, str(i + 1), (x - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(image, str(i + 1), (x - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
        if len(corner_coordinates) > 0:
            image_path = 'image_'+ time.strftime('%d%H%M%S')+'.jpg'
            cv2.imwrite(image_path, image)
            print("Saved image to:", image_path)
                
        cv2.namedWindow("image", cv2.WINDOW_AUTOSIZE)
        cv2.imshow("image", image)
        # image_path = 'image_'+ time.strftime('%d%H%M%S')+'.jpg'
        # cv2.imwrite(image_path, image)
        # print("Saved image to:", image_path)
        
        #time_end = time.time()
        #print('time cos:', time_end - time_start, 's')
        #print("帧率：",1/(time_end - time_start))
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break
            
    # 输出九个角点坐标
    interest_corner = input("请输入9个数字，以空格分隔(否则使用默认角点)：")
    print(len(interest_corner.split()))
    interest_corner = [int(num) for num in interest_corner.split()] if len(interest_corner.split()) == 9 else [8, 10, 12, 20, 22, 24, 32, 34, 36]
    print("选择用于标定的角点列表为：", interest_corner)

    #interest_corner = [8, 10, 12, 20, 22, 24, 32, 34, 36] # 后边会减，这里不用减一
    if len(corner_coordinates) >= 9:
        print("九个标记的角点坐标：")
        for i in range(9):
            print(f"[{(corner_coordinates[interest_corner[i] - 1])[0]}, {(corner_coordinates[interest_corner[i] - 1])[1]}],")
            #print(f"角点 {interest_corner[i]}: {corner_coordinates[interest_corner[i] - 1]}")
    else:
        print("未能找到足够的角点。")
    
    # 关闭设备
    close_device(cam, data_buf)

    return [corner_coordinates[index - 1] for index in interest_corner]

def showImage():
    while True:
        #time_start = time.time()
        
        image = get_image(data_buf, nPayloadSize)
        #print(image.shape)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        #print(image.shape)
        image = cv2.rotate(image, cv2.ROTATE_180)
        image = cv2.resize(image, dsize=(640, 480))
        # cv2.line(image,(90,0),(90,486),(0,0,255),3)
        cv2.namedWindow("image", cv2.WINDOW_AUTOSIZE)
        cv2.imshow("image", image)
        # image_path = 'image_'+ time.strftime('%d%H%M%S')+'.jpg'
        # cv2.imwrite(image_path, image)
        # print("Saved image to:", image_path)
        
        #time_end = time.time()
        #print('time cos:', time_end - time_start, 's')
        #print("帧率：",1/(time_end - time_start))
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break
    
    # 关闭设备
    close_device(cam, data_buf)
    
def getImage():
    while True:
        #time_start = time.time()
        
        image = get_image(data_buf, nPayloadSize)
        #print(image.shape)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        #print(image.shape)
        image = cv2.rotate(image, cv2.ROTATE_180)
        image = cv2.resize(image, dsize=(640, 480))
        # cv2.line(image,(90,0),(90,486),(0,0,255),3)

        # image_path = 'image_'+ time.strftime('%d%H%M%S')+'.jpg'
        # cv2.imwrite(image_path, image)
        # print("Saved image to:", image_path)
        
        return image

        
def closeDevice():
    # 关闭设备
    close_device(cam, data_buf)

# 获得设备信息
deviceList = MV_CC_DEVICE_INFO_LIST()
tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE
# ch: 枚举设备 | en:Enum device
# nTLayerType[IN] 枚举传输层 ，pstDevList[OUT] 设备列表
Enum_device(tlayerType, deviceList)

# 获取相机和图像数据缓存区
cam, data_buf, nPayloadSize = enable_device(0)  # 选择第一个设备

cam.MV_CC_SetFloatValue("ExposureTime", 260000.0)


if __name__ == "__main__":
    print("作为单独脚本运行，默认输出图像信息...")
    showImage()
