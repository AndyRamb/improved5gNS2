//
// Copyright (C) 2004 Andras Varga
//
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU Lesser General Public License
// as published by the Free Software Foundation; either version 2
// of the License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Lesser General Public License for more details.
//
// You should have received a copy of the GNU Lesser General Public License
// along with this program; if not, see <http://www.gnu.org/licenses/>.
//

#ifndef __INET_TcpSimpleSshAppV2lite_H
#define __INET_TcpSimpleSshAppV2lite_H

#include "inet/common/INETDefs.h"

#include "inet/applications/tcpapp/TcpAppBase.h"
#include "inet/common/lifecycle/LifecycleOperation.h"
#include "inet/transportlayer/contract/tcp/TcpSocket.h"

#include "TcpRttListener.h"

#include <list>

namespace inet {

/**
 * An example Telnet client application. The server app should be TcpGenericServerApp.
 */
class INET_API TcpSimpleSshAppV2lite : public TcpAppBase//, public TcpSocket
{
  protected:
    cMessage *timeoutMsg = nullptr;
    int numLinesToType = 0;    // lines (commands) the user will type in this session
    int numCharsToType = 0;    // characters the user will type for current line (command)
    simtime_t stopTime;

    int64_t expectingBytes;
    bool commandOutputReceived;

    simsignal_t rttSignal;
    simsignal_t mosValueSignal;

    simtime_t sendTime;
    double finalRTT;
    unsigned long uniqueIdentifier;

    TcpRttListener *listener;

  protected:
    virtual int numInitStages() const override { return NUM_INIT_STAGES; }
    virtual void initialize(int stage) override;
    virtual void handleTimer(cMessage *msg) override;
    virtual void socketEstablished(TcpSocket *socket) override;
    virtual void socketDataArrived(TcpSocket *socket, Packet *msg, bool urgent) override;
    virtual void socketClosed(TcpSocket *socket) override;
    virtual void socketFailure(TcpSocket *socket, int code) override;
    virtual void checkedScheduleAt(simtime_t t, cMessage *msg);
    virtual void sendGenericAppMsg(int numBytes, int expectedReplyBytes);

    virtual void handleStartOperation(LifecycleOperation *operation) override;
    virtual void handleStopOperation(LifecycleOperation *operation) override;
    virtual void handleCrashOperation(LifecycleOperation *operation) override;
  public:
    TcpSimpleSshAppV2lite() {}
    virtual ~TcpSimpleSshAppV2lite();


};

} // namespace inet

#endif // ifndef __INET_TcpSimpleSshAppV2lite_H

