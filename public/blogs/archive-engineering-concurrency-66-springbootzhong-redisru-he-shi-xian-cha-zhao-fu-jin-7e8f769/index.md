# SpringBoot中，Redis如何实现查找附近的人功能？

# 1、先看效果
UserLocationController.http
# 2、核心代码
```java
com.itsoku.lesson066.controller.UserLocationController
```
![image-20240719184649529](/blogs/_archive-2024-assets/dbaf070dd9f0cb8bbb12.webp)
# 3、原理
附近的人是使用Redis中的Geo（Geospatial）数据结构实现的。
Redis的Geo功能允许我们存储地理位置信息，并提供了根据地理位置查询数据的各种功能，比如本文中的查询附近的人功能。
使用主要2个步骤
### 1）添加地理位置数据
首先，先geoadd命令，将用户位置信息添加到redis中，如下
```bash
GEOADD users:locations 121.245996 31.114995 user1  
GEOADD users:locations 121.241343 31.113264 user2  
GEOADD users:locations 121.356703 31.161321 user3
...
```
## 2）查询附近的人
使用`GEORADIUS`命令来查询指定范围内的用户
```bash
GEORADIUS users:locations 121.2439 31.114678 1000 m WITHDIST WITHCOORD COUNT 10 ASC
```
上面这条命令：查找以(116.405285, 39.904989)为中心，半径为1000米内的最近的10个用户，并返回用户ID、距离、和坐标
# 源码
com.itsoku.lesson066.controller.UserLocationController
```java
package com.itsoku.lesson066.controller;
import com.itsoku.lesson066.dto.NearbyUserDto;
import com.itsoku.lesson066.dto.AddUserLocationReq;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.geo.*;
import org.springframework.data.redis.connection.RedisGeoCommands;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.domain.geo.Metrics;
import org.springframework.web.bind.annotation.*;
import java.util.ArrayList;
import java.util.List;
/**
 * <b>description</b>实战
 * <b>time</b>：2024/7/18 20:23 <br>
 * <b>author</b>：gjy
 */
@RestController
public class UserLocationController {
    @Autowired
    private StringRedisTemplate stringRedisTemplate;
    /**
     * 批量将用户地理位置信息添加到redis中（实际工作中，大家可以提供一个用户地理位置上报的接口，客户端可以每隔10秒，上报一下地理位置坐标，将其丢到redis中）
     *
     * @param userLocationReqList
     * @return
     */
    @PostMapping("/addUserLocation")
    public boolean addUserLocation(@RequestBody List<AddUserLocationReq> userLocationReqList) {
        String key = "users:locations";
        for (AddUserLocationReq userLocationReq : userLocationReqList) {
            String userId = userLocationReq.getUserId();
            Double longitude = userLocationReq.getLongitude();
            Double latitude = userLocationReq.getLatitude();
            this.stringRedisTemplate.opsForGeo().add(key, new Point(longitude, latitude), userId);
        }
        return true;
    }
    /**
     * 获取附近的人列表，以（longitude,latitude）为圆心，以 radius 为半径，获取count个用户
     *
     * @param longitude 进度
     * @param latitude  纬度
     * @param radius    圆的半径（米）
     * @param count     获取用户的数量
     * @return
     */
    @GetMapping("/findNearbyUserList")
    public List<NearbyUserDto> findNearbyUserList(@RequestParam("longitude") double longitude,
                                                 @RequestParam("latitude") double latitude,
                                                 @RequestParam("radius") double radius,
                                                 @RequestParam("count") int count) {
        List<NearbyUserDto> nearbyUserDtoList = new ArrayList<>();
        //从redis中获取附近的用户列表
        String key = "users:locations";
        Circle circle = new Circle(new Point(longitude, latitude), new Distance(radius, Metrics.METERS));
        RedisGeoCommands.GeoRadiusCommandArgs args = RedisGeoCommands.GeoRadiusCommandArgs
                .newGeoRadiusArgs()
                .includeCoordinates()
                .includeDistance()
                .sortAscending().limit(count);
        GeoResults<RedisGeoCommands.GeoLocation<String>> geoResults = stringRedisTemplate.opsForGeo().radius(key, circle, args);
        List<GeoResult<RedisGeoCommands.GeoLocation<String>>> content = geoResults.getContent();
        for (GeoResult<RedisGeoCommands.GeoLocation<String>> geoResultGeoResult : content) {
            RedisGeoCommands.GeoLocation<String> geoLocation = geoResultGeoResult.getContent();
            Point point = geoLocation.getPoint();
            String userId = geoLocation.getName();
            //拿到用于的id、经纬度、距离
            NearbyUserDto nearbyUserDto = new NearbyUserDto();
            nearbyUserDto.setUserId(userId);
            nearbyUserDto.setLongitude(point.getX());
            nearbyUserDto.setLatitude(point.getY());
            nearbyUserDto.setDistance(geoResultGeoResult.getDistance().getValue());
            nearbyUserDtoList.add(nearbyUserDto);
        }
        return nearbyUserDtoList;
    }
}
```
